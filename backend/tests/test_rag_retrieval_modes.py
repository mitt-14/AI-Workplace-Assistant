from unittest.mock import patch

from app.rag.rag_service import retrieve_context


def test_retrieve_context_uses_semantic_search() -> None:
    expected = [
        {
            "chunk_id": "semantic-1",
            "relevance_score": 0.9,
        }
    ]

    with patch(
        "app.rag.rag_service.semantic_search",
        return_value=expected,
    ) as mocked_search:
        results = retrieve_context(
            query="password requirements",
            top_k=5,
            document_id=None,
            retrieval_mode="semantic",
        )

    mocked_search.assert_called_once()
    assert results == expected


def test_retrieve_context_uses_keyword_search() -> None:
    expected = [
        {
            "chunk_id": "keyword-1",
            "keyword_score": 5.0,
        }
    ]

    with patch(
        "app.rag.rag_service.keyword_search",
        return_value=expected,
    ) as mocked_search:
        results = retrieve_context(
            query="RTO",
            top_k=5,
            document_id=None,
            retrieval_mode="keyword",
        )

    mocked_search.assert_called_once()
    assert results == expected


def test_retrieve_context_uses_hybrid_search() -> None:
    expected = [
        {
            "chunk_id": "hybrid-1",
            "hybrid_score": 0.8,
        }
    ]

    with patch(
        "app.rag.rag_service.hybrid_search",
        return_value=expected,
    ) as mocked_search:
        results = retrieve_context(
            query="incident response",
            top_k=5,
            document_id=None,
            retrieval_mode="hybrid",
        )

    mocked_search.assert_called_once()
    assert results == expected