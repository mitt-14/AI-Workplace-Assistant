from __future__ import annotations
import logging

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.conversation_store import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)
from app.core.exceptions import (
    ConversationNotFoundError,
    SemanticSearchError,
)
from app.rag.hybrid_retriever import hybrid_search
from app.rag.keyword_retriever import keyword_search
from app.rag.prompt_builder import build_rag_prompt
from app.rag.query_rewriter import rewrite_search_query
from app.rag.retriever import semantic_search


logger = logging.getLogger(__name__)


RetrievalMode = Literal[
    "semantic",
    "keyword",
    "hybrid",
]


@dataclass
class PreparedRAGRequest:
    """
    Data prepared before invoking or streaming an LLM response.
    """

    conversation_id: str
    question: str
    provider: str
    retrieval_query: str
    retrieval_mode: RetrievalMode
    conversation_history: list[dict[str, Any]]
    search_results: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    prompt: str | None


def extract_model_answer(response: Any) -> str:
    """
    Extract plain text from a LangChain model response.
    """

    if hasattr(response, "content"):
        content = response.content

        if isinstance(content, str):
            return content.strip()

        return str(content).strip()

    if isinstance(response, str):
        return response.strip()

    return str(response).strip()


def extract_stream_chunk_text(chunk: Any) -> str:
    """
    Extract text from a streamed LangChain model chunk.

    Whitespace is not stripped because spaces between streamed
    chunks must be preserved.
    """

    if hasattr(chunk, "content"):
        content = chunk.content
    else:
        content = chunk

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if isinstance(text, str):
                    text_parts.append(text)

        return "".join(text_parts)

    if content is None:
        return ""

    return str(content)


def optional_float(value: Any) -> float | None:
    """
    Safely convert a value to float while preserving None.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def optional_int(value: Any) -> int | None:
    """
    Safely convert a value to int while preserving None.
    """

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_sources(
    search_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert retrieved document chunks into API source objects.
    """

    sources: list[dict[str, Any]] = []

    for result in search_results:
        text = str(
            result.get("text", "")
        ).strip()

        text_preview = text[:300]

        if len(text) > 300:
            text_preview += "..."

        retrieval_methods = result.get(
            "retrieval_methods",
            [],
        )

        if not isinstance(retrieval_methods, list):
            retrieval_methods = []

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
                "page_number": optional_int(
                    result.get("page_number")
                ),
                "chunk_index": optional_int(
                    result.get("chunk_index")
                ),
                "page_chunk_index": optional_int(
                    result.get("page_chunk_index")
                ),
                "relevance_score": optional_float(
                    result.get("relevance_score")
                ),
                "keyword_score": optional_float(
                    result.get("keyword_score")
                ),
                "normalized_semantic_score": optional_float(
                    result.get(
                        "normalized_semantic_score"
                    )
                ),
                "normalized_keyword_score": optional_float(
                    result.get(
                        "normalized_keyword_score"
                    )
                ),
                "hybrid_score": optional_float(
                    result.get("hybrid_score")
                ),
                "retrieval_methods": [
                    str(method)
                    for method in retrieval_methods
                ],
                "text_preview": text_preview,
            }
        )

    return sources


def retrieve_context(
    *,
    query: str,
    top_k: int,
    document_id: str | None,
    retrieval_mode: RetrievalMode,
) -> list[dict[str, Any]]:
    """
    Retrieve chunks using the selected retrieval method.
    """

    if retrieval_mode == "semantic":
        candidate_count = min(
            top_k * 3,
            settings.maximum_search_results,
        )

        search_results = semantic_search(
            query=query,
            top_k=candidate_count,
            document_id=document_id,
        )

        relevant_results = [
            result
            for result in search_results
            if float(
                result.get(
                    "relevance_score",
                    0.0,
                )
            )
            >= settings.minimum_relevance_score
        ]

        for result in relevant_results:
            result.setdefault(
                "retrieval_methods",
                ["semantic"],
            )

        return relevant_results[:top_k]

    if retrieval_mode == "keyword":
        search_results = keyword_search(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )

        for result in search_results:
            result.setdefault(
                "retrieval_methods",
                ["keyword"],
            )

        return search_results

    if retrieval_mode == "hybrid":
        return hybrid_search(
            query=query,
            top_k=top_k,
            document_id=document_id,
            semantic_weight=settings.hybrid_semantic_weight,
            keyword_weight=settings.hybrid_keyword_weight,
        )

    raise ValueError(
        f"Unsupported retrieval mode: {retrieval_mode}"
    )


def resolve_conversation_id(
    *,
    conversation_id: str | None,
    question: str,
) -> str:
    """
    Create a conversation or validate an existing conversation.
    """

    if conversation_id is None:
        conversation = create_conversation(
            title=question[:80],
        )

        return str(
            conversation["conversation_id"]
        )

    if get_conversation(conversation_id) is None:
        raise ConversationNotFoundError(
            conversation_id
        )

    return conversation_id


def save_assistant_message(
    *,
    conversation_id: str,
    answer: str,
    provider: str,
    sources: list[dict[str, Any]],
) -> None:
    """
    Save a completed assistant response to conversation storage.
    """

    add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        provider=provider,
        sources=sources,
    )


def prepare_rag_request(
    *,
    question: str,
    provider: str,
    top_k: int,
    document_id: str | None = None,
    conversation_id: str | None = None,
    retrieval_mode: RetrievalMode = "hybrid",
) -> PreparedRAGRequest:
    """
    Prepare everything required before generating an LLM answer.

    This function performs:

    1. Question validation
    2. Conversation creation or validation
    3. Conversation-history loading
    4. Follow-up query rewriting
    5. User-message storage
    6. Semantic, keyword, or hybrid retrieval
    7. Source construction
    8. Prompt construction
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        raise SemanticSearchError(
            "The RAG question cannot be empty."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    if retrieval_mode not in {
        "semantic",
        "keyword",
        "hybrid",
    }:
        raise ValueError(
            f"Unsupported retrieval mode: {retrieval_mode}"
        )

    resolved_conversation_id = resolve_conversation_id(
        conversation_id=conversation_id,
        question=cleaned_question,
    )

    # Load previous messages before saving the current question.
    conversation_history = get_messages(
        resolved_conversation_id,
        limit=settings.maximum_conversation_messages,
    )

    retrieval_query = rewrite_search_query(
        question=cleaned_question,
        conversation_history=conversation_history,
        provider=provider,
    )

    add_message(
        conversation_id=resolved_conversation_id,
        role="user",
        content=cleaned_question,
    )

    logger.info(
        "Preparing RAG request: provider=%s top_k=%s "
        "retrieval_mode=%s document_id=%s "
        "conversation_id=%s",
        provider,
        top_k,
        retrieval_mode,
        document_id,
        resolved_conversation_id,
    )

    search_results = retrieve_context(
        query=retrieval_query,
        top_k=top_k,
        document_id=document_id,
        retrieval_mode=retrieval_mode,
    )

    sources = build_sources(
        search_results
    )

    prompt: str | None = None

    if search_results:
        prompt = build_rag_prompt(
            question=cleaned_question,
            search_results=search_results,
            conversation_history=conversation_history,
        )

    logger.info(
        "RAG request prepared: conversation_id=%s "
        "retrieval_mode=%s retrieved_count=%s",
        resolved_conversation_id,
        retrieval_mode,
        len(search_results),
    )

    return PreparedRAGRequest(
        conversation_id=resolved_conversation_id,
        question=cleaned_question,
        provider=provider,
        retrieval_query=retrieval_query,
        retrieval_mode=retrieval_mode,
        conversation_history=conversation_history,
        search_results=search_results,
        sources=sources,
        prompt=prompt,
    )


def answer_with_documents(
    *,
    question: str,
    provider: str,
    top_k: int,
    document_id: str | None = None,
    conversation_id: str | None = None,
    retrieval_mode: RetrievalMode = "hybrid",
) -> dict[str, Any]:
    """
    Generate a complete non-streaming RAG response.
    """

    prepared = prepare_rag_request(
        question=question,
        provider=provider,
        top_k=top_k,
        document_id=document_id,
        conversation_id=conversation_id,
        retrieval_mode=retrieval_mode,
    )

    if not prepared.search_results:
        answer = (
            "I could not find enough information "
            "in the indexed documents."
        )

        save_assistant_message(
            conversation_id=prepared.conversation_id,
            answer=answer,
            provider=prepared.provider,
            sources=[],
        )

        logger.info(
            "RAG request completed without results: "
            "conversation_id=%s retrieval_mode=%s",
            prepared.conversation_id,
            prepared.retrieval_mode,
        )

        return {
            "conversation_id": prepared.conversation_id,
            "retrieval_query": prepared.retrieval_query,
            "retrieval_mode": prepared.retrieval_mode,
            "answer": answer,
            "search_results": [],
            "sources": [],
        }

    if prepared.prompt is None:
        raise RuntimeError(
            "RAG prompt was not created for retrieved results."
        )

    try:
        model = get_model(
            prepared.provider
        )

        model_response = model.invoke(
            prepared.prompt
        )

        answer = extract_model_answer(
            model_response
        )

    except Exception:
        logger.exception(
            "RAG model generation failed: "
            "provider=%s conversation_id=%s",
            prepared.provider,
            prepared.conversation_id,
        )
        raise

    if not answer:
        answer = (
            "I could not generate an answer from "
            "the retrieved document context."
        )

    save_assistant_message(
        conversation_id=prepared.conversation_id,
        answer=answer,
        provider=prepared.provider,
        sources=prepared.sources,
    )

    logger.info(
        "RAG request completed: provider=%s "
        "retrieval_mode=%s retrieved_chunks=%s "
        "conversation_id=%s",
        prepared.provider,
        prepared.retrieval_mode,
        len(prepared.search_results),
        prepared.conversation_id,
    )

    return {
        "conversation_id": prepared.conversation_id,
        "retrieval_query": prepared.retrieval_query,
        "retrieval_mode": prepared.retrieval_mode,
        "answer": answer,
        "search_results": prepared.search_results,
        "sources": prepared.sources,
    }


def stream_answer_with_documents(
    *,
    question: str,
    provider: str,
    top_k: int,
    document_id: str | None = None,
    conversation_id: str | None = None,
    retrieval_mode: RetrievalMode = "hybrid",
) -> Iterator[dict[str, Any]]:
    """
    Stream a grounded RAG response as structured events.

    The complete assistant answer is saved after model streaming
    finishes successfully.
    """

    prepared = prepare_rag_request(
        question=question,
        provider=provider,
        top_k=top_k,
        document_id=document_id,
        conversation_id=conversation_id,
        retrieval_mode=retrieval_mode,
    )

    yield {
        "event": "start",
        "data": {
            "conversation_id": prepared.conversation_id,
            "question": prepared.question,
            "retrieval_query": prepared.retrieval_query,
            "retrieval_mode": prepared.retrieval_mode,
            "provider": prepared.provider,
        },
    }

    if not prepared.search_results:
        answer = (
            "I could not find enough information "
            "in the indexed documents."
        )

        save_assistant_message(
            conversation_id=prepared.conversation_id,
            answer=answer,
            provider=prepared.provider,
            sources=[],
        )

        yield {
            "event": "sources",
            "data": {
                "retrieval_mode": prepared.retrieval_mode,
                "retrieved_chunk_count": 0,
                "sources": [],
            },
        }

        yield {
            "event": "token",
            "data": {
                "content": answer,
            },
        }

        yield {
            "event": "done",
            "data": {
                "conversation_id": prepared.conversation_id,
                "retrieval_mode": prepared.retrieval_mode,
                "status": "completed",
            },
        }

        logger.info(
            "Streaming RAG request completed without results: "
            "conversation_id=%s retrieval_mode=%s",
            prepared.conversation_id,
            prepared.retrieval_mode,
        )

        return

    if prepared.prompt is None:
        yield {
            "event": "error",
            "data": {
                "conversation_id": prepared.conversation_id,
                "message": (
                    "The RAG prompt could not be created."
                ),
            },
        }

        return

    yield {
        "event": "sources",
        "data": {
            "retrieval_mode": prepared.retrieval_mode,
            "retrieved_chunk_count": len(
                prepared.search_results
            ),
            "sources": prepared.sources,
        },
    }

    answer_chunks: list[str] = []

    try:
        model = get_model(
            prepared.provider
        )

        for chunk in model.stream(
            prepared.prompt
        ):
            text = extract_stream_chunk_text(
                chunk
            )

            if not text:
                continue

            answer_chunks.append(text)

            yield {
                "event": "token",
                "data": {
                    "content": text,
                },
            }

    except GeneratorExit:
        logger.warning(
            "Streaming client disconnected: "
            "conversation_id=%s",
            prepared.conversation_id,
        )
        return

    except Exception:
        logger.exception(
            "Streaming RAG generation failed: "
            "provider=%s conversation_id=%s",
            prepared.provider,
            prepared.conversation_id,
        )

        yield {
            "event": "error",
            "data": {
                "conversation_id": prepared.conversation_id,
                "message": (
                    "The model could not generate "
                    "the streamed answer."
                ),
            },
        }

        return

    answer = "".join(
        answer_chunks
    ).strip()

    if not answer:
        answer = (
            "I could not generate an answer from "
            "the retrieved document context."
        )

        yield {
            "event": "token",
            "data": {
                "content": answer,
            },
        }

    save_assistant_message(
        conversation_id=prepared.conversation_id,
        answer=answer,
        provider=prepared.provider,
        sources=prepared.sources,
    )

    logger.info(
        "Streaming RAG request completed: provider=%s "
        "retrieval_mode=%s retrieved_chunks=%s "
        "conversation_id=%s",
        prepared.provider,
        prepared.retrieval_mode,
        len(prepared.search_results),
        prepared.conversation_id,
    )

    yield {
        "event": "done",
        "data": {
            "conversation_id": prepared.conversation_id,
            "retrieval_mode": prepared.retrieval_mode,
            "status": "completed",
        },
    }