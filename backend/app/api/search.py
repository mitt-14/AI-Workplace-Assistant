import logging

from fastapi import APIRouter

from app.core.config import settings
from app.rag.retriever import semantic_search
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
)

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=SemanticSearchResponse,
    summary="Search indexed documents semantically",
)
async def search_documents(
    request: SemanticSearchRequest,
) -> SemanticSearchResponse:
    top_k = min(
        request.top_k,
        settings.maximum_search_results,
    )

    results = semantic_search(
        query=request.query,
        top_k=top_k,
        document_id=request.document_id,
    )

    logger.info(
        "Search request completed: query=%s result_count=%s",
        request.query,
        len(results),
    )

    return SemanticSearchResponse(
        query=request.query,
        result_count=len(results),
        embedding_model=settings.embedding_model,
        results=results,
        status="completed",
    )