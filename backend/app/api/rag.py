import logging

from fastapi import APIRouter

from app.core.config import settings
from app.rag.rag_service import answer_with_documents
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
    )

    sources = [
        RagSource(**source)
        for source in result["sources"]
    ]

    logger.info(
        "RAG API request completed: provider=%s "
        "source_count=%s",
        request.provider,
        len(sources),
    )

    return RagChatResponse(
        question=request.question,
        answer=result["answer"],
        provider=request.provider,
        embedding_model=settings.embedding_model,
        retrieved_chunk_count=len(
            result["search_results"]
        ),
        sources=sources,
        status="completed",
    )