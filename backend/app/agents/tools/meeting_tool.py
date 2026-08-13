from typing import Any

from app.schemas.meeting_analysis import (
    MeetingAnalysisRequest,
)
from app.services.meeting_analyzer import (
    analyze_meeting,
)


async def analyze_meeting_with_agent(
    *,
    transcript: str,
    provider: str | None = None,
    title: str | None = None,
    generate_follow_up_email: bool = False,
    follow_up_email_style: str = "professional",
) -> dict[str, Any]:
    if not transcript.strip():
        raise ValueError(
            "transcript is required."
        )

    request = MeetingAnalysisRequest(
        title=title,
        transcript=transcript,
        provider=provider,
        generate_follow_up_email=(
            generate_follow_up_email
        ),
        follow_up_email_style=(
            follow_up_email_style
        ),
    )

    result = await analyze_meeting(
        request
    )

    return result.model_dump(
        mode="json"
    )
