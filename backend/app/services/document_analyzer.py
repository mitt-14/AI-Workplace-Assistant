from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.exceptions import (
    ApplicationError,
    DocumentAnalysisError,
    DocumentAnalysisNotFoundError,
    DocumentAnalysisParseError,
    DocumentIndexingError,
    DocumentNotFoundError,
    LLMServiceError,
)
from app.rag.document_loader import ExtractedDocument, extract_document_pages
from app.schemas.document_analysis import (
    ActionItemPriority,
    DocumentActionItem,
    DocumentAnalysisContent,
    DocumentAnalysisListItem,
    DocumentAnalysisResponse,
    DocumentRisk,
    RiskSeverity,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisChunk:
    chunk_number: int
    text: str
    page_numbers: list[int]


def _load_document_metadata(document_id: str) -> dict[str, Any]:
    metadata_path = Path(settings.upload_directory) / f"{document_id}.json"
    if not metadata_path.exists():
        raise DocumentNotFoundError(document_id)

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Failed to read document metadata: document_id=%s", document_id)
        raise DocumentIndexingError("The stored document metadata could not be read.") from exc

    required = {"document_id", "original_filename", "stored_filename", "content_type"}
    if not required.issubset(metadata):
        raise DocumentIndexingError("The stored document metadata is incomplete.")
    return metadata


def _get_document_path(document_id: str, metadata: dict[str, Any]) -> Path:
    file_path = Path(settings.upload_directory) / Path(str(metadata["stored_filename"])).name
    if not file_path.exists() or not file_path.is_file():
        raise DocumentNotFoundError(document_id)
    return file_path


def _split_text_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        pieces.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


def _build_analysis_chunks(extracted: ExtractedDocument) -> tuple[list[AnalysisChunk], int, bool]:
    """Create page-aware chunks while keeping the number of LLM calls small."""
    configured_limit = max(500, settings.document_analysis_chunk_characters)
    overlap = max(0, min(settings.document_analysis_chunk_overlap_characters, configured_limit // 5))
    maximum_chunks = max(1, settings.document_analysis_max_chunks)

    total_characters = sum(len(page.text) for page in extracted.pages)
    if total_characters == 0:
        return [], 0, False

    # Raise the effective chunk size when needed so a large document does not
    # create dozens of slow local-model requests.
    minimum_size_for_limit = (total_characters + maximum_chunks - 1) // maximum_chunks
    chunk_limit = max(configured_limit, minimum_size_for_limit)

    chunks: list[AnalysisChunk] = []
    current_sections: list[str] = []
    current_pages: list[int] = []
    current_length = 0
    was_truncated = False

    def flush() -> None:
        nonlocal current_sections, current_pages, current_length
        if not current_sections:
            return
        chunks.append(
            AnalysisChunk(
                chunk_number=len(chunks) + 1,
                text="\n\n".join(current_sections).strip(),
                page_numbers=sorted(set(current_pages)),
            )
        )
        current_sections = []
        current_pages = []
        current_length = 0

    for page in extracted.pages:
        page_text = page.text.strip()
        if not page_text:
            continue
        label = f"--- PAGE {page.page_number} ---\n"
        available = max(1, chunk_limit - len(label))
        page_parts = _split_text_with_overlap(page_text, available, overlap)

        for part in page_parts:
            section = f"{label}{part.strip()}"
            if current_sections and current_length + len(section) + 2 > chunk_limit:
                flush()
            current_sections.append(section)
            current_pages.append(page.page_number)
            current_length += len(section) + 2

            if len(chunks) >= maximum_chunks:
                was_truncated = True
                break
        if was_truncated:
            break

    if not was_truncated:
        flush()
    elif current_sections and len(chunks) < maximum_chunks:
        flush()

    if len(chunks) > maximum_chunks:
        chunks = chunks[:maximum_chunks]
        was_truncated = True

    return chunks, total_characters, was_truncated


def _build_chunk_prompt(filename: str, chunk: AnalysisChunk) -> str:
    return f"""
You are a strict JSON API analyzing one section of an enterprise document.
Return ONLY one valid compact JSON object. Do not use Markdown or commentary.
Use only facts supported by this section.

Schema:
{{"executive_summary":"Brief section summary","key_points":["Important point"],"risks":[{{"title":"Risk title","description":"Evidence-based explanation","severity":"medium","page_numbers":[1]}}],"action_items":[{{"task":"Explicit or clearly required action","priority":"medium","owner":null,"deadline":null,"page_numbers":[1]}}],"recommendations":["Practical recommendation"]}}

Rules:
- severity: low, medium, high, critical.
- priority: low, medium, high, urgent.
- Use [] when unsupported.
- Maximum 5 key points, 3 risks, 3 action items, 3 recommendations.
- Page numbers only from {chunk.page_numbers}.
- owner and deadline are null unless explicitly stated.
- Keep the complete response concise.

Filename: {filename}
Chunk: {chunk.chunk_number}
Document section:
{chunk.text}
""".strip()


def _extract_response_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "".join(parts).strip()
    return str(content).strip()


def _extract_json_object(response_text: str) -> dict[str, Any]:
    cleaned = response_text.strip()
    if not cleaned:
        raise DocumentAnalysisParseError()

    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        logger.warning("No JSON object found in document analysis response")
        raise DocumentAnalysisParseError()

    candidate = cleaned[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            parsed = json.loads(repaired)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse analysis JSON: error=%s", exc)
            raise DocumentAnalysisParseError() from exc

    if not isinstance(parsed, dict):
        raise DocumentAnalysisParseError()
    return parsed


def _validate_content(response_text: str, document_id: str, stage: str) -> DocumentAnalysisContent:
    try:
        return DocumentAnalysisContent.model_validate(_extract_json_object(response_text))
    except ValidationError as exc:
        logger.warning(
            "Document analysis validation failed: document_id=%s stage=%s errors=%s",
            document_id,
            stage,
            exc.errors(),
        )
        raise DocumentAnalysisParseError() from exc


def _normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\b(risk|risks|of|the|a|an|due|to|with|company)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _similar(left: str, right: str, threshold: float = 0.72) -> bool:
    left_key, right_key = _normalize_text(left), _normalize_text(right)
    if not left_key or not right_key:
        return False
    if left_key in right_key or right_key in left_key:
        return True
    left_tokens, right_tokens = set(left_key.split()), set(right_key.split())
    union = left_tokens | right_tokens
    token_score = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return token_score >= 0.55 or SequenceMatcher(None, left_key, right_key).ratio() >= threshold


def _dedupe_strings(values: list[str], limit: int) -> list[str]:
    output: list[str] = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value.strip())
        if not cleaned or any(_similar(cleaned, existing, 0.78) for existing in output):
            continue
        output.append(cleaned)
        if len(output) >= limit:
            break
    return output


def _severity_rank(value: RiskSeverity) -> int:
    return {RiskSeverity.low: 1, RiskSeverity.medium: 2, RiskSeverity.high: 3, RiskSeverity.critical: 4}[value]


def _priority_rank(value: ActionItemPriority) -> int:
    return {ActionItemPriority.low: 1, ActionItemPriority.medium: 2, ActionItemPriority.high: 3, ActionItemPriority.urgent: 4}[value]


def _build_executive_summary(analyses: list[DocumentAnalysisContent], key_points: list[str]) -> str:
    summaries = _dedupe_strings([item.executive_summary for item in analyses], 3)
    generic_prefixes = ("this section", "detailed operational guidance", "the section")
    useful = [summary for summary in summaries if not summary.lower().startswith(generic_prefixes)]
    if useful:
        return " ".join(useful)[:900].strip()
    if key_points:
        preview = "; ".join(key_points[:5])
        return f"The document defines key workplace policies, responsibilities, controls, and compliance requirements. Major points include: {preview}."[:900]
    return "The document was analyzed successfully and contains workplace policies, responsibilities, risks, and recommended actions."


def _deterministic_merge(analyses: list[DocumentAnalysisContent]) -> DocumentAnalysisContent:
    key_points = _dedupe_strings([value for analysis in analyses for value in analysis.key_points], 15)

    risks: list[DocumentRisk] = []
    for analysis in analyses:
        for risk in analysis.risks:
            match = next((existing for existing in risks if _similar(risk.title, existing.title)), None)
            if match:
                match.page_numbers = sorted(set(match.page_numbers + risk.page_numbers))
                if _severity_rank(risk.severity) > _severity_rank(match.severity):
                    match.severity = risk.severity
                if len(risk.description) > len(match.description):
                    match.description = risk.description
            else:
                copied = risk.model_copy(deep=True)
                copied.page_numbers = sorted(set(copied.page_numbers))
                risks.append(copied)

    actions: list[DocumentActionItem] = []
    for analysis in analyses:
        for action in analysis.action_items:
            match = next((existing for existing in actions if _similar(action.task, existing.task)), None)
            if match:
                match.page_numbers = sorted(set(match.page_numbers + action.page_numbers))
                if _priority_rank(action.priority) > _priority_rank(match.priority):
                    match.priority = action.priority
                match.owner = match.owner or action.owner
                match.deadline = match.deadline or action.deadline
            else:
                copied = action.model_copy(deep=True)
                copied.page_numbers = sorted(set(copied.page_numbers))
                actions.append(copied)

    recommendations = _dedupe_strings(
        [value for analysis in analyses for value in analysis.recommendations],
        10,
    )

    return DocumentAnalysisContent(
        executive_summary=_build_executive_summary(analyses, key_points),
        key_points=key_points,
        risks=risks[:10],
        action_items=actions[:10],
        recommendations=recommendations,
    )


async def _invoke_model(model: Any, prompt: str, document_id: str, provider: str, stage: str) -> str:
    try:
        response = await model.ainvoke(prompt)
    except ApplicationError:
        raise
    except Exception as exc:
        logger.exception(
            "Document analysis LLM request failed: document_id=%s provider=%s stage=%s",
            document_id,
            provider,
            stage,
        )
        raise LLMServiceError(
            message=f"The {provider} service could not analyze the document. Check whether the model service and configuration are available."
        ) from exc

    text = _extract_response_text(response)
    logger.debug(
        "Document analysis response received: document_id=%s provider=%s stage=%s characters=%s",
        document_id,
        provider,
        stage,
        len(text),
    )
    return text


def _analysis_directory() -> Path:
    directory = Path(settings.document_analysis_directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _analysis_path(analysis_id: str) -> Path:
    return _analysis_directory() / f"{Path(analysis_id).name}.json"


def _save_analysis(response: DocumentAnalysisResponse) -> None:
    try:
        _analysis_path(response.analysis_id).write_text(response.model_dump_json(indent=2), encoding="utf-8")
    except OSError as exc:
        logger.exception("Failed to save document analysis: analysis_id=%s", response.analysis_id)
        raise DocumentAnalysisError("The analysis was generated but could not be saved.") from exc


def _find_cached_analysis(document_id: str, provider: str) -> DocumentAnalysisResponse | None:
    if not settings.document_analysis_cache_enabled:
        return None
    candidates: list[DocumentAnalysisResponse] = []
    for path in _analysis_directory().glob("*.json"):
        try:
            analysis = DocumentAnalysisResponse.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            continue
        if analysis.document_id == document_id and analysis.provider == provider and analysis.status == "completed":
            candidates.append(analysis)
    if not candidates:
        return None
    cached = max(candidates, key=lambda item: item.created_at)
    return cached.model_copy(update={"cached": True})


async def _analyze_chunk(
    *,
    chunk: AnalysisChunk,
    chunk_count: int,
    model: Any,
    filename: str,
    document_id: str,
    provider: str,
    semaphore: asyncio.Semaphore,
) -> tuple[int, DocumentAnalysisContent]:
    async with semaphore:
        logger.info(
            "Analyzing document chunk: document_id=%s chunk=%s/%s pages=%s characters=%s",
            document_id,
            chunk.chunk_number,
            chunk_count,
            chunk.page_numbers,
            len(chunk.text),
        )
        raw = await _invoke_model(
            model,
            _build_chunk_prompt(filename, chunk),
            document_id,
            provider,
            f"chunk_{chunk.chunk_number}",
        )
        return chunk.chunk_number, _validate_content(raw, document_id, f"chunk_{chunk.chunk_number}")


async def analyze_document(
    *,
    document_id: str,
    provider: str | None = None,
    refresh: bool = False,
) -> DocumentAnalysisResponse:
    started = time.perf_counter()
    selected_provider = (provider or settings.default_llm_provider).strip().lower()

    if not refresh:
        cached = _find_cached_analysis(document_id, selected_provider)
        if cached is not None:
            logger.info("Returning cached document analysis: document_id=%s analysis_id=%s", document_id, cached.analysis_id)
            return cached

    metadata = _load_document_metadata(document_id)
    file_path = _get_document_path(document_id, metadata)
    extracted = extract_document_pages(file_path=file_path, content_type=str(metadata["content_type"]))
    chunks, original_character_count, was_truncated = _build_analysis_chunks(extracted)
    if not chunks:
        raise DocumentAnalysisError("No analyzable document chunks were created.")

    model = get_model(selected_provider)
    concurrency = max(1, min(settings.document_analysis_concurrency, len(chunks)))
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        _analyze_chunk(
            chunk=chunk,
            chunk_count=len(chunks),
            model=model,
            filename=str(metadata["original_filename"]),
            document_id=document_id,
            provider=selected_provider,
            semaphore=semaphore,
        )
        for chunk in chunks
    ]
    indexed_results = await asyncio.gather(*tasks)
    indexed_results.sort(key=lambda item: item[0])
    chunk_analyses = [content for _, content in indexed_results]
    analyzed_character_count = sum(len(chunk.text) for chunk in chunks)

    if len(chunk_analyses) == 1:
        final_content = chunk_analyses[0]
        strategy = "single_chunk"
    else:
        # A Python merge is faster and more reliable than an extra local LLM call.
        final_content = _deterministic_merge(chunk_analyses)
        strategy = "chunked_parallel_deterministic_merge"

    model_name = getattr(model, "model", getattr(model, "model_name", None))
    response = DocumentAnalysisResponse(
        analysis_id=str(uuid4()),
        document_id=document_id,
        filename=str(metadata["original_filename"]),
        content_type=str(metadata["content_type"]),
        provider=selected_provider,
        model=str(model_name) if model_name is not None else None,
        page_count=extracted.total_pages,
        readable_page_count=len(extracted.pages),
        original_character_count=original_character_count,
        analyzed_character_count=analyzed_character_count,
        was_truncated=was_truncated,
        chunk_count=len(chunks),
        analyzed_chunk_count=len(chunk_analyses),
        analysis_strategy=strategy,
        processing_time_seconds=round(time.perf_counter() - started, 3),
        cached=False,
        executive_summary=final_content.executive_summary,
        key_points=final_content.key_points,
        risks=final_content.risks,
        action_items=final_content.action_items,
        recommendations=final_content.recommendations,
        created_at=datetime.now(timezone.utc),
        status="completed",
    )
    _save_analysis(response)
    logger.info(
        "Document analysis completed: document_id=%s analysis_id=%s provider=%s chunks=%s concurrency=%s seconds=%s strategy=%s",
        document_id,
        response.analysis_id,
        selected_provider,
        len(chunks),
        concurrency,
        response.processing_time_seconds,
        strategy,
    )
    return response


def get_document_analysis(analysis_id: str) -> DocumentAnalysisResponse:
    path = _analysis_path(analysis_id)
    if not path.exists():
        raise DocumentAnalysisNotFoundError(analysis_id)
    try:
        return DocumentAnalysisResponse.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DocumentAnalysisError("The saved document analysis could not be read.") from exc
    except ValidationError as exc:
        raise DocumentAnalysisError("The saved document analysis is invalid.") from exc


def list_document_analyses() -> list[DocumentAnalysisListItem]:
    analyses: list[DocumentAnalysisListItem] = []
    for path in _analysis_directory().glob("*.json"):
        try:
            analysis = DocumentAnalysisResponse.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            logger.exception("Skipping unreadable analysis file: path=%s", path)
            continue
        analyses.append(
            DocumentAnalysisListItem(
                analysis_id=analysis.analysis_id,
                document_id=analysis.document_id,
                filename=analysis.filename,
                provider=analysis.provider,
                created_at=analysis.created_at,
                status=analysis.status,
            )
        )
    analyses.sort(key=lambda item: item.created_at, reverse=True)
    return analyses
