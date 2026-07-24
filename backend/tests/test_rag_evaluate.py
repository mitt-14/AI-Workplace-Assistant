from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.exceptions import (
    ConversationNotFoundError,
    SemanticSearchError,
)
from app.rag.rag_service import evaluate_retrieval


SAMPLE_RESULTS = [
    {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "filename": "policy.pdf",
        "text": "Employees may work remotely two days per week.",
        "relevance_score": 0.9,
        "keyword_score": 4.0,
        "hybrid_score": 0.85,
        "retrieval_methods": ["semantic", "keyword"],
    },
    {
        "chunk_id": "chunk-2",
        "document_id": "doc-2",
        "filename": "handbook.pdf",
        "text": "Return-to-office exceptions require manager approval.",
        "relevance_score": 0.7,
        "keyword_score": 2.0,
        "hybrid_score": 0.65,
        "retrieval_methods": ["semantic", "keyword"],
    },
]


def test_evaluate_retrieval_returns_results_sources_and_metrics() -> None:
    with (
        patch(
            "app.rag.rag_service.rewrite_search_query",
            return_value="remote work return to office policy",
        ) as mocked_rewrite,
        patch(
            "app.rag.rag_service.retrieve_context",
            return_value=SAMPLE_RESULTS,
        ) as mocked_retrieve,
        patch("app.rag.rag_service.get_model") as mocked_get_model,
    ):
        result = evaluate_retrieval(
            question="What is the RTO policy?",
            provider="ollama",
            top_k=5,
            retrieval_mode="hybrid",
        )

    assert result["question"] == "What is the RTO policy?"
    assert result["retrieval_query"] == (
        "remote work return to office policy"
    )
    assert result["retrieval_mode"] == "hybrid"
    assert result["search_results"] == SAMPLE_RESULTS
    assert len(result["sources"]) == 2

    metrics = result["metrics"]
    assert metrics["retrieved_chunk_count"] == 2
    assert metrics["documents_retrieved"] == 2
    assert metrics["average_relevance_score"] == 0.8
    assert metrics["highest_relevance_score"] == 0.9
    assert metrics["lowest_relevance_score"] == 0.7
    assert metrics["average_keyword_score"] == 3.0
    assert metrics["average_hybrid_score"] == 0.75
    assert metrics["average_chunk_length"] > 0
    assert metrics["retrieval_time_ms"] >= 0
    assert metrics["generation_time_ms"] == 0.0
    assert metrics["total_time_ms"] == metrics["retrieval_time_ms"]

    mocked_rewrite.assert_called_once_with(
        question="What is the RTO policy?",
        conversation_history=[],
        provider="ollama",
    )
    mocked_retrieve.assert_called_once_with(
        query="remote work return to office policy",
        top_k=5,
        document_id=None,
        document_ids=None,
        retrieval_mode="hybrid",
    )
    mocked_get_model.assert_not_called()


def test_evaluate_retrieval_returns_empty_metrics() -> None:
    with (
        patch(
            "app.rag.rag_service.rewrite_search_query",
            return_value="missing policy",
        ),
        patch(
            "app.rag.rag_service.retrieve_context",
            return_value=[],
        ),
    ):
        result = evaluate_retrieval(
            question="What is the missing policy?",
            provider="ollama",
            top_k=3,
            retrieval_mode="semantic",
        )

    assert result["search_results"] == []
    assert result["sources"] == []
    assert result["metrics"]["retrieved_chunk_count"] == 0
    assert result["metrics"]["documents_retrieved"] == 0
    assert result["metrics"]["average_relevance_score"] is None
    assert result["metrics"]["average_keyword_score"] is None
    assert result["metrics"]["average_hybrid_score"] is None
    assert result["metrics"]["average_chunk_length"] is None


def test_evaluate_retrieval_passes_document_filters() -> None:
    with (
        patch(
            "app.rag.rag_service.rewrite_search_query",
            return_value="incident response",
        ),
        patch(
            "app.rag.rag_service.retrieve_context",
            return_value=[],
        ) as mocked_retrieve,
    ):
        evaluate_retrieval(
            question="Explain incident response.",
            provider="gemini",
            top_k=4,
            document_id="doc-primary",
            document_ids=["doc-1", "doc-2"],
            retrieval_mode="keyword",
        )

    mocked_retrieve.assert_called_once_with(
        query="incident response",
        top_k=4,
        document_id="doc-primary",
        document_ids=["doc-1", "doc-2"],
        retrieval_mode="keyword",
    )


def test_evaluate_retrieval_uses_existing_conversation_history() -> None:
    history = [
        {
            "role": "user",
            "content": "Tell me about remote work.",
        }
    ]

    with (
        patch(
            "app.rag.rag_service.get_conversation",
            return_value={"conversation_id": "conversation-1"},
        ),
        patch(
            "app.rag.rag_service.get_messages",
            return_value=history,
        ),
        patch(
            "app.rag.rag_service.rewrite_search_query",
            return_value="remote work eligibility",
        ) as mocked_rewrite,
        patch(
            "app.rag.rag_service.retrieve_context",
            return_value=[],
        ),
    ):
        evaluate_retrieval(
            question="Who is eligible?",
            provider="ollama",
            top_k=3,
            conversation_id="conversation-1",
            retrieval_mode="hybrid",
        )

    mocked_rewrite.assert_called_once_with(
        question="Who is eligible?",
        conversation_history=history,
        provider="ollama",
    )


def test_evaluate_retrieval_rejects_unknown_conversation() -> None:
    with patch(
        "app.rag.rag_service.get_conversation",
        return_value=None,
    ):
        with pytest.raises(ConversationNotFoundError):
            evaluate_retrieval(
                question="What is the policy?",
                provider="ollama",
                top_k=3,
                conversation_id="missing-conversation",
                retrieval_mode="hybrid",
            )


def test_evaluate_retrieval_rejects_blank_question() -> None:
    with pytest.raises(SemanticSearchError):
        evaluate_retrieval(
            question="   ",
            provider="ollama",
            top_k=3,
            retrieval_mode="hybrid",
        )