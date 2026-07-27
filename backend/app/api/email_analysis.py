from fastapi import APIRouter

from app.schemas.email_analysis import (
    BatchEmailAnalysisRequest,
    BatchEmailAnalysisResponse,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
    EmailReplyRequest,
    EmailReplyResponse,
)
from app.services.email_analyzer import (
    analyze_email,
    analyze_email_batch,
    generate_email_reply,
)

router = APIRouter(prefix="/email", tags=["Email Assistant"])


@router.post(
    "/analyze",
    response_model=EmailAnalysisResponse,
    summary="Analyze an email",
)
async def analyze_email_endpoint(
    request: EmailAnalysisRequest,
) -> EmailAnalysisResponse:
    return await analyze_email(request)


@router.post(
    "/reply",
    response_model=EmailReplyResponse,
    summary="Generate an email reply",
)
async def generate_email_reply_endpoint(
    request: EmailReplyRequest,
) -> EmailReplyResponse:
    return await generate_email_reply(request)


@router.post(
    "/batch",
    response_model=BatchEmailAnalysisResponse,
    summary="Analyze multiple emails",
)
async def analyze_email_batch_endpoint(
    request: BatchEmailAnalysisRequest,
) -> BatchEmailAnalysisResponse:
    return await analyze_email_batch(request)
