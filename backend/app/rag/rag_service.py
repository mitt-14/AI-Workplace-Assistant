import logging
from typing import Any

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.exceptions import SemanticSearchError
from app.rag.prompt_builder import build_rag_prompt
from app.rag.retriever import semantic_search

logger = logging.getLogger(__name__)


def extract_model_answer(response: Any) -> str:
    """
    Extract text from a LangChain model response.
    """

    if hasattr(response, "content"):
        content = response.content

        if isinstance(content, str):
            return content.strip()

        return str(content).strip()

    if isinstance(response, str):
        return response.strip()

    return str(response).strip()


def build_sources(
    search_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert search results into API source objects.
    """

    sources: list[dict[str, Any]] = []

    for result in search_results:
        text = str(
            result.get("text", "")
        ).strip()

        text_preview = text[:300]

        if len(text) > 300:
            text_preview += "..."

        sources.append(
            {
                "chunk_id": str(
                    result.get("chunk_id", "")
                ),
                "document_id": str(
                    result.get("document_id", "")
                ),
                "filename": str(
                    result.get(
                        "filename",
                        "Unknown document",
                    )
                ),
                "chunk_index": int(
                    result.get("chunk_index", 0)
                ),
                "relevance_score": float(
                    result.get(
                        "relevance_score",
                        0.0,
                    )
                ),
                "text_preview": text_preview,
            }
        )

    return sources


def answer_with_documents(
    *,
    question: str,
    provider: str,
    top_k: int,
    document_id: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve document chunks and generate a grounded answer.
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        raise SemanticSearchError(
            "The RAG question cannot be empty."
        )

    logger.info(
        "Starting RAG request: provider=%s top_k=%s "
        "document_id=%s",
        provider,
        top_k,
        document_id,
    )

    candidate_count = min(
    top_k * 3,
    settings.maximum_search_results,
    )
    search_results = semantic_search(
        query=cleaned_question,
        top_k=top_k,
        document_id=document_id,
    )

    relevant_results = [
    result
    for result in search_results
    if float(result.get("relevance_score", 0.0))
    >= settings.minimum_relevance_score
    ]

    relevant_results = relevant_results[:top_k]
    
    if not relevant_results:
        return {
            "answer": (
                "I could not find enough information "
                "in the indexed documents."
            ),
            "search_results": [],
            "sources": [],
        }

    prompt = build_rag_prompt(
        question=cleaned_question,
        search_results=relevant_results,
    )

    try:
        model = get_model(provider)

        model_response = model.invoke(prompt)

        answer = extract_model_answer(
            model_response
        )

    except Exception:
        logger.exception(
            "RAG model generation failed: provider=%s",
            provider,
        )
        raise

    if not answer:
        answer = (
            "I could not generate an answer from "
            "the retrieved document context."
        )

    sources = build_sources(
        relevant_results
    )

    logger.info(
        "RAG request completed: provider=%s "
        "retrieved_chunks=%s model=%s",
        provider,
        len(relevant_results),
        settings.embedding_model,
    )

    return {
        "answer": answer,
        "search_results": relevant_results,
        "sources": sources,
    }