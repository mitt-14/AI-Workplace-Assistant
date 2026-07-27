import asyncio
import logging
import re
import time
from uuid import uuid4
from typing import Any

from pydantic import ValidationError

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.exceptions import EmailAnalysisError, EmailAnalysisParseError, LLMServiceError
from app.prompts.email_analysis_prompt import (
    build_email_analysis_prompt,
    build_email_reply_prompt,
)
from app.schemas.email_analysis import (
    BatchEmailAnalysisRequest,
    BatchEmailAnalysisResponse,
    BatchEmailAnalysisResult,
    EmailAnalysisContent,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
    EmailClassification,
    EmailPriority,
    EmailReplyRequest,
    EmailReplyResponse,
    EmailRisk,
    EmailRiskSeverity,
    EmailRiskType,
    EmailSentiment,
)
from app.utils.email_utils import (
    extract_deterministic_entities,
    extract_json_object,
    response_to_text,
    unique_strings,
)

logger = logging.getLogger(__name__)

_URGENT_TERMS = re.compile(r"\b(urgent|asap|immediately|critical|today|within\s+\d+\s+hours?)\b", re.I)
_HIGH_TERMS = re.compile(r"\b(deadline|overdue|blocked|cannot access|security incident|breach|payment due)\b", re.I)
_NEGATIVE_TERMS = re.compile(r"\b(unacceptable|angry|frustrated|disappointed|failed|failure|problem|issue|complaint)\b", re.I)
_POSITIVE_TERMS = re.compile(r"\b(thank you|thanks|great|excellent|pleased|happy|appreciate)\b", re.I)
_PHISHING_TERMS = re.compile(r"\b(verify your account|confirm your password|login immediately|gift card|wire transfer|crypto wallet|seed phrase)\b", re.I)
_TASK_TERMS = re.compile(r"\b(please|must|need to|kindly|action required|could you|can you)\b", re.I)


def _provider(provider: str | None) -> str:
    return (provider or settings.default_llm_provider).strip().lower()


def _model_name(model: Any) -> str | None:
    for attribute in ("model", "model_name"):
        value = getattr(model, attribute, None)
        if isinstance(value, str):
            return value
    return None


async def _invoke(model: Any, prompt: str, provider: str, stage: str) -> str:
    try:
        response = await model.ainvoke(prompt)
        text = response_to_text(response)
    except Exception as exc:
        logger.exception("Email LLM request failed: provider=%s stage=%s", provider, stage)
        raise LLMServiceError("The email-analysis language model request failed.") from exc
    if not text:
        raise LLMServiceError("The email-analysis language model returned an empty response.")
    return text


def _merge_entities(content: EmailAnalysisContent, request: EmailAnalysisRequest) -> None:
    deterministic = extract_deterministic_entities(
        request.subject,
        request.sender,
        request.recipients,
        request.body,
    )
    content.entities.email_addresses = unique_strings(
        [*content.entities.email_addresses, *deterministic.email_addresses]
    )
    content.entities.phone_numbers = unique_strings(
        [*content.entities.phone_numbers, *deterministic.phone_numbers]
    )
    content.entities.urls = unique_strings([*content.entities.urls, *deterministic.urls])
    content.entities.monetary_amounts = unique_strings(
        [*content.entities.monetary_amounts, *deterministic.monetary_amounts]
    )


def _heuristic_analysis(request: EmailAnalysisRequest) -> EmailAnalysisContent:
    text = f"{request.subject or ''}\n{request.body}".strip()
    lowered = text.casefold()

    classification = EmailClassification.general
    if _PHISHING_TERMS.search(text):
        classification = EmailClassification.phishing
    elif any(term in lowered for term in ("invoice", "payment", "bank", "expense", "refund")):
        classification = EmailClassification.finance
    elif any(term in lowered for term in ("meeting", "calendar", "appointment", "schedule")):
        classification = EmailClassification.meeting
    elif any(term in lowered for term in ("error", "bug", "login", "server", "technical")):
        classification = EmailClassification.technical
    elif any(term in lowered for term in ("complaint", "unacceptable", "disappointed")):
        classification = EmailClassification.complaint
    elif any(term in lowered for term in ("job", "employee", "leave", "vacation", "hr")):
        classification = EmailClassification.hr

    if _URGENT_TERMS.search(text):
        priority = EmailPriority.urgent
    elif _HIGH_TERMS.search(text):
        priority = EmailPriority.high
    else:
        priority = EmailPriority.medium

    negative = bool(_NEGATIVE_TERMS.search(text))
    positive = bool(_POSITIVE_TERMS.search(text))
    sentiment = EmailSentiment.mixed if negative and positive else (
        EmailSentiment.negative if negative else EmailSentiment.positive if positive else EmailSentiment.neutral
    )

    sentences = [
        " ".join(sentence.split())
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", request.body)
        if sentence.strip()
    ]
    key_points = unique_strings(sentences, limit=5)
    summary = " ".join(key_points[:2])[:700] or "Email received for review."

    tasks = []
    for sentence in sentences:
        if _TASK_TERMS.search(sentence):
            tasks.append({"task": sentence[:500], "priority": priority.value})
            if len(tasks) == 5:
                break

    risks: list[EmailRisk] = []
    if classification == EmailClassification.phishing:
        risks.append(
            EmailRisk(
                type=EmailRiskType.phishing,
                severity=EmailRiskSeverity.high,
                description="The email contains language commonly associated with credential or payment phishing.",
                evidence=_PHISHING_TERMS.search(text).group(0) if _PHISHING_TERMS.search(text) else None,
            )
        )

    content = EmailAnalysisContent(
        classification=classification,
        priority=priority,
        sentiment=sentiment,
        summary=summary,
        key_points=key_points,
        tasks=tasks,
        risks=risks,
        suggested_reply=None,
        confidence=0.35,
    )
    _merge_entities(content, request)
    return content


async def analyze_email(request: EmailAnalysisRequest) -> EmailAnalysisResponse:
    started = time.perf_counter()
    provider = _provider(request.provider)
    model = get_model(provider)
    prompt = build_email_analysis_prompt(request)

    raw = await _invoke(model, prompt, provider, "analysis")
    payload = extract_json_object(raw)
    strategy = "llm_structured"

    if payload is None:
        logger.warning("Email analysis returned no JSON; using deterministic fallback")
        content = _heuristic_analysis(request)
        strategy = "deterministic_fallback"
    else:
        try:
            content = EmailAnalysisContent.model_validate(payload)
            _merge_entities(content, request)
        except ValidationError as exc:
            logger.warning("Email analysis JSON validation failed: %s", exc)
            content = _heuristic_analysis(request)
            strategy = "deterministic_fallback"

    if request.generate_reply and not content.suggested_reply:
        reply_request = EmailReplyRequest(
            subject=request.subject,
            sender=request.sender,
            recipients=request.recipients,
            body=request.body,
            provider=provider,
            style=request.reply_style,
            custom_instructions=request.custom_reply_instructions,
        )
        reply = await generate_email_reply(reply_request, model=model)
        content.suggested_reply = reply.reply

    return EmailAnalysisResponse(
        analysis_id=str(uuid4()),
        provider=provider,
        model=_model_name(model),
        processing_time_seconds=round(time.perf_counter() - started, 3),
        analysis_strategy=strategy,
        **content.model_dump(),
    )


async def generate_email_reply(
    request: EmailReplyRequest,
    model: Any | None = None,
) -> EmailReplyResponse:
    started = time.perf_counter()
    provider = _provider(request.provider)
    selected_model = model or get_model(provider)
    raw = await _invoke(
        selected_model,
        build_email_reply_prompt(request),
        provider,
        "reply",
    )
    reply = raw.strip().strip('`').strip()
    if not reply:
        raise EmailAnalysisError("The email reply could not be generated.")
    return EmailReplyResponse(
        reply=reply,
        provider=provider,
        model=_model_name(selected_model),
        style=request.style,
        processing_time_seconds=round(time.perf_counter() - started, 3),
    )


async def analyze_email_batch(
    request: BatchEmailAnalysisRequest,
) -> BatchEmailAnalysisResponse:
    started = time.perf_counter()
    semaphore = asyncio.Semaphore(settings.email_analysis_batch_concurrency)

    async def process(item: Any) -> BatchEmailAnalysisResult:
        async with semaphore:
            try:
                analysis_request = EmailAnalysisRequest(
                    subject=item.subject,
                    sender=item.sender,
                    recipients=item.recipients,
                    body=item.body,
                    provider=request.provider,
                    generate_reply=request.generate_reply,
                    reply_style=request.reply_style,
                )
                analysis = await analyze_email(analysis_request)
                return BatchEmailAnalysisResult(email_id=item.email_id, analysis=analysis)
            except Exception as exc:
                logger.exception("Batch email analysis failed: email_id=%s", item.email_id)
                return BatchEmailAnalysisResult(email_id=item.email_id, error=str(exc))

    results = await asyncio.gather(*(process(item) for item in request.emails))
    succeeded = sum(result.analysis is not None for result in results)
    return BatchEmailAnalysisResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
        processing_time_seconds=round(time.perf_counter() - started, 3),
    )
