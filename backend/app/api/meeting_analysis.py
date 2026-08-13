from fastapi import APIRouter

from app.schemas.meeting_analysis import (
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    MeetingFollowUpRequest,
    MeetingFollowUpResponse,
)
from app.services.meeting_analyzer import (
    analyze_meeting,
    generate_meeting_follow_up,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Meeting Assistant"],
)


@router.post(
    "/analyze",
    response_model=MeetingAnalysisResponse,
    summary="Analyze a meeting transcript",
)
async def analyze_meeting_endpoint(
    request: MeetingAnalysisRequest,
) -> MeetingAnalysisResponse:
    return await analyze_meeting(
        request
    )


@router.post(
    "/follow-up",
    response_model=MeetingFollowUpResponse,
    summary="Generate a meeting follow-up email",
)
async def generate_meeting_follow_up_endpoint(
    request: MeetingFollowUpRequest,
) -> MeetingFollowUpResponse:
    return await generate_meeting_follow_up(
        request
    )
