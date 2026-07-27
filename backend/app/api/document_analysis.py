import logging

from fastapi import APIRouter, Query

from app.schemas.document_analysis import (
    DocumentAnalysisListResponse,
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
)
from app.services.document_analyzer import (
    analyze_document,
    get_document_analysis,
    list_document_analyses,
)

router = APIRouter(
    prefix="/document-analysis",
    tags=["Document Analysis"],
)

logger = logging.getLogger(__name__)


@router.post(
    "/{document_id}/analyze",
    response_model=DocumentAnalysisResponse,
    status_code=201,
    summary="Analyze an uploaded document",
)
async def analyze_uploaded_document(
    document_id: str,
    request: DocumentAnalysisRequest,
    refresh: bool = Query(default=False, description="Force a new analysis instead of returning a cached result."),
) -> DocumentAnalysisResponse:
    return await analyze_document(
        document_id=document_id,
        provider=request.provider,
        refresh=refresh,
    )


@router.get(
    "",
    response_model=DocumentAnalysisListResponse,
    summary="List saved document analyses",
)
async def list_saved_document_analyses() -> DocumentAnalysisListResponse:
    analyses = list_document_analyses()

    return DocumentAnalysisListResponse(
        total=len(analyses),
        analyses=analyses,
    )


@router.get(
    "/{analysis_id}",
    response_model=DocumentAnalysisResponse,
    summary="Get one saved document analysis",
)
async def get_saved_document_analysis(
    analysis_id: str,
) -> DocumentAnalysisResponse:
    return get_document_analysis(analysis_id)
