import logging
import json
from collections.abc import Iterator
from typing import Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.rag.rag_service import (
    answer_with_documents,
    stream_answer_with_documents,
)
from app.schemas.rag import (
    RagChatRequest,
    RagChatResponse,
    RagSource,
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

logger = logging.getLogger(__name__)

def encode_sse_event(
    event: dict[str, Any],
) -> str:
    """
    Convert a structured event into Server-Sent Events format.
    """

    event_name = str(
        event.get("event", "message")
    )

    event_data = json.dumps(
        event.get("data", {}),
        ensure_ascii=False,
    )

    return (
        f"event: {event_name}\n"
        f"data: {event_data}\n\n"
    )


@router.post(
    "/chat",
    response_model=RagChatResponse,
    summary="Answer questions using indexed documents",
)
async def rag_chat(
    request: RagChatRequest,
) -> RagChatResponse:
    top_k = min(
        request.top_k,
        settings.maximum_search_results,
    )

    result = answer_with_documents(
        question=request.question,
        provider=request.provider,
        top_k=top_k,
        document_id=request.document_id,
        conversation_id=request.conversation_id,
    )

    sources = [
        RagSource(**source)
        for source in result["sources"]
    ]

    logger.info(
        "RAG API request completed: provider=%s "
        "source_count=%s conversation_id=%s",
        request.provider,
        len(sources),
        result["conversation_id"],
    )

    return RagChatResponse(
        conversation_id=result[
            "conversation_id"
        ],
        question=request.question,
        retrieval_query=result["retrieval_query"],
        answer=result["answer"],
        provider=request.provider,
        embedding_model=settings.embedding_model,
        retrieved_chunk_count=len(
            result["search_results"]
        ),
        sources=sources,
        status="completed",
    )

@router.post(
    "/chat/stream",
    summary="Stream answers using indexed documents",
    response_class=StreamingResponse,
)
async def stream_rag_chat(
    request: RagChatRequest,
) -> StreamingResponse:
    """
    Stream a conversation-aware RAG answer using SSE.
    """

    top_k = min(
        request.top_k,
        settings.maximum_search_results,
    )

    def event_generator() -> Iterator[str]:
        events = stream_answer_with_documents(
            question=request.question,
            provider=request.provider,
            top_k=top_k,
            document_id=request.document_id,
            conversation_id=request.conversation_id,
        )

        for event in events:
            yield encode_sse_event(
                event
            )

    logger.info(
        "Starting streaming RAG API request: "
        "provider=%s conversation_id=%s",
        request.provider,
        request.conversation_id,
    )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )