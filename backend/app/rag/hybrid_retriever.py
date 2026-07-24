from __future__ import annotations

import logging
from typing import Any

from app.rag.keyword_retriever import keyword_search
from app.rag.retriever import semantic_search

logger = logging.getLogger(__name__)


def normalize_semantic_score(score: float | None) -> float:
    """
    Convert a semantic relevance score to the 0–1 range.
    """

    if score is None:
        return 0.0

    return max(0.0, min(1.0, float(score)))


def normalize_keyword_scores(
    results: list[dict[str, Any]],
) -> None:
    """
    Normalize BM25 scores in-place using the highest score
    from the current result set.
    """

    if not results:
        return

    maximum = max(
        float(result.get("keyword_score", 0.0))
        for result in results
    )

    if maximum <= 0:
        maximum = 1.0

    for result in results:
        keyword_score = float(
            result.get("keyword_score", 0.0)
        )

        result["normalized_keyword_score"] = (
            keyword_score / maximum
        )

def build_chunk_key(
    result: dict[str, Any],
) -> str:
    """
    Build a stable identifier for deduplicating chunks.

    Prefer the Chroma chunk ID. Fall back to document and
    chunk metadata if a chunk ID is unavailable.
    """

    chunk_id = result.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    document_id = result.get("document_id", "")
    page_number = result.get("page_number", "")
    chunk_index = result.get("chunk_index", "")
    text = result.get("text", "")

    return (
        f"{document_id}:"
        f"{page_number}:"
        f"{chunk_index}:"
        f"{hash(text)}"
    )

def hybrid_search(
    *,
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Combine semantic and BM25 retrieval results.

    The function:
    - retrieves candidates from both retrievers
    - normalizes their scores
    - merges duplicate chunks
    - calculates a weighted hybrid score
    - returns the best-ranked chunks
    """

    if not query.strip():
        return []

    if top_k <= 0:
        return []

    if semantic_weight < 0 or keyword_weight < 0:
        raise ValueError(
            "semantic_weight and keyword_weight must be non-negative."
        )

    total_weight = semantic_weight + keyword_weight

    if total_weight <= 0:
        raise ValueError(
            "At least one retrieval weight must be greater than zero."
        )

    semantic_weight = semantic_weight / total_weight
    keyword_weight = keyword_weight / total_weight

    candidate_count = max(top_k * 2, top_k)

    semantic_results = semantic_search(
        query=query,
        top_k=candidate_count,
        document_id=document_id,
    )

    keyword_results = keyword_search(
        query=query,
        top_k=candidate_count,
        document_id=document_id,
    )

    normalize_keyword_scores(keyword_results)

    for result in semantic_results:
        result["normalized_semantic_score"] = (
            normalize_semantic_score(
                result.get("relevance_score")
            )
        )

    merged_results: dict[str, dict[str, Any]] = {}

    for result in semantic_results:
        chunk_key = build_chunk_key(result)

        merged_results[chunk_key] = {
            **result,
            "normalized_semantic_score": result.get(
                "normalized_semantic_score",
                0.0,
            ),
            "normalized_keyword_score": 0.0,
            "retrieval_methods": ["semantic"],
        }

    for result in keyword_results:
        chunk_key = build_chunk_key(result)

        normalized_keyword_score = float(
            result.get("normalized_keyword_score", 0.0)
        )

        if chunk_key in merged_results:
            existing = merged_results[chunk_key]

            existing["keyword_score"] = result.get(
                "keyword_score",
                0.0,
            )

            existing["normalized_keyword_score"] = (
                normalized_keyword_score
            )

            existing["retrieval_methods"] = [
                "semantic",
                "keyword",
            ]

            for field in (
                "document_id",
                "filename",
                "content_type",
                "page_number",
                "chunk_index",
                "page_chunk_index",
                "character_count",
                "text",
            ):
                if existing.get(field) is None:
                    existing[field] = result.get(field)

        else:
            merged_results[chunk_key] = {
                **result,
                "relevance_score": 0.0,
                "normalized_semantic_score": 0.0,
                "normalized_keyword_score": (
                    normalized_keyword_score
                ),
                "retrieval_methods": ["keyword"],
            }

    ranked_results: list[dict[str, Any]] = []

    for result in merged_results.values():
        semantic_score = float(
            result.get("normalized_semantic_score", 0.0)
        )

        keyword_score = float(
            result.get("normalized_keyword_score", 0.0)
        )

        hybrid_score = (
            semantic_weight * semantic_score
            + keyword_weight * keyword_score
        )

        result["hybrid_score"] = round(
            hybrid_score,
            6,
        )

        result["semantic_weight"] = semantic_weight
        result["keyword_weight"] = keyword_weight

        ranked_results.append(result)

    ranked_results.sort(
        key=lambda result: (
            result.get("hybrid_score", 0.0),
            result.get("normalized_semantic_score", 0.0),
            result.get("normalized_keyword_score", 0.0),
        ),
        reverse=True,
    )

    logger.debug(
        (
            "Hybrid search completed: query=%r, "
            "semantic_candidates=%d, keyword_candidates=%d, "
            "merged_candidates=%d, returned=%d"
        ),
        query,
        len(semantic_results),
        len(keyword_results),
        len(merged_results),
        min(top_k, len(ranked_results)),
    )

    return ranked_results[:top_k]