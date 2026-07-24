from __future__ import annotations

import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

from app.rag.vector_store import (
    get_all_document_chunks,
)

logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    """
    Lowercase tokenizer for BM25.
    """

    return TOKEN_PATTERN.findall(
        text.lower()
    )

def build_bm25_index(
    documents: list[str],
) -> BM25Okapi:

    tokenized = [
        tokenize(doc)
        for doc in documents
    ]

    return BM25Okapi(tokenized)

def keyword_search(
    *,
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Perform BM25 keyword search over indexed document chunks.
    """

    stored = get_all_document_chunks(
        document_id=document_id,
        document_ids=document_ids,
    )

    documents = stored.get("documents") or []
    metadatas = stored.get("metadatas") or []
    ids = stored.get("ids") or []

    if not documents:
        logger.warning(
            "No indexed documents available for keyword search."
        )
        return []

    bm25 = build_bm25_index(documents)

    tokenized_query = tokenize(query)

    scores = bm25.get_scores(tokenized_query)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]

    results: list[dict[str, Any]] = []

    for index, score in ranked:

        metadata = metadatas[index] or {}

        results.append(
            {
                "chunk_id": ids[index],
                "document_id": metadata.get("document_id"),
                "filename": metadata.get("filename"),
                "content_type": metadata.get(
                    "content_type"
                ),
                "page_number": metadata.get(
                    "page_number"
                ),
                "chunk_index": metadata.get(
                    "chunk_index"
                ),
                "page_chunk_index": metadata.get(
                    "page_chunk_index"
                ),
                "character_count": metadata.get(
                    "character_count"
                ),
                "text": documents[index],
                "keyword_score": float(score),
            }
        )

    return results