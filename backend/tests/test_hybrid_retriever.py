from __future__ import annotations

from unittest.mock import patch

from app.rag.hybrid_retriever import hybrid_search


def test_hybrid_search_merges_same_chunk() -> None:
    semantic_results = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "filename": "policy.pdf",
            "page_number": 2,
            "chunk_index": 5,
            "text": "Passwords must be at least 16 characters.",
            "relevance_score": 0.8,
        }
    ]

    keyword_results = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "filename": "policy.pdf",
            "page_number": 2,
            "chunk_index": 5,
            "text": "Passwords must be at least 16 characters.",
            "keyword_score": 10.0,
        }
    ]

    with patch(
        "app.rag.hybrid_retriever.semantic_search",
        return_value=semantic_results,
    ), patch(
        "app.rag.hybrid_retriever.keyword_search",
        return_value=keyword_results,
    ):
        results = hybrid_search(
            query="password requirements",
            top_k=5,
        )

    assert len(results) == 1
    assert results[0]["chunk_id"] == "chunk-1"
    assert results[0]["retrieval_methods"] == [
        "semantic",
        "keyword",
    ]
    assert results[0]["normalized_semantic_score"] == 0.8
    assert results[0]["normalized_keyword_score"] == 1.0
    assert results[0]["hybrid_score"] == 0.86


def test_hybrid_search_keeps_unique_results() -> None:
    semantic_results = [
        {
            "chunk_id": "semantic-1",
            "text": "Semantic result",
            "relevance_score": 0.9,
        }
    ]

    keyword_results = [
        {
            "chunk_id": "keyword-1",
            "text": "Keyword result",
            "keyword_score": 5.0,
        }
    ]

    with patch(
        "app.rag.hybrid_retriever.semantic_search",
        return_value=semantic_results,
    ), patch(
        "app.rag.hybrid_retriever.keyword_search",
        return_value=keyword_results,
    ):
        results = hybrid_search(
            query="test",
            top_k=5,
        )

    assert len(results) == 2

    methods = {
        result["chunk_id"]: result["retrieval_methods"]
        for result in results
    }

    assert methods["semantic-1"] == ["semantic"]
    assert methods["keyword-1"] == ["keyword"]


def test_hybrid_search_returns_top_k_results() -> None:
    semantic_results = [
        {
            "chunk_id": f"chunk-{index}",
            "text": f"Result {index}",
            "relevance_score": 1.0 - index * 0.1,
        }
        for index in range(5)
    ]

    with patch(
        "app.rag.hybrid_retriever.semantic_search",
        return_value=semantic_results,
    ), patch(
        "app.rag.hybrid_retriever.keyword_search",
        return_value=[],
    ):
        results = hybrid_search(
            query="test",
            top_k=2,
        )

    assert len(results) == 2
    assert results[0]["chunk_id"] == "chunk-0"
    assert results[1]["chunk_id"] == "chunk-1"


def test_hybrid_search_returns_empty_for_blank_query() -> None:
    results = hybrid_search(
        query="   ",
        top_k=5,
    )

    assert results == []


def test_hybrid_search_rejects_invalid_weights() -> None:
    try:
        hybrid_search(
            query="test",
            semantic_weight=-1,
            keyword_weight=1,
        )

        assert False, "Expected ValueError"

    except ValueError as error:
        assert "non-negative" in str(error)