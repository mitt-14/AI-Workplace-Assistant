from typing import Any

from app.schemas.email_analysis import (
    EmailAnalysisRequest,
    ReplyStyle,
)
from app.services.email_analyzer import analyze_email


async def analyze_email_with_agent(
    *,
    body: str,
    provider: str | None = None,
    subject: str | None = None,
    sender: str | None = None,
    recipients: list[str] | None = None,
    generate_reply: bool = False,
    reply_style: str = "professional",
) -> dict[str, Any]:
    if not body.strip():
        raise ValueError(
            "body is required."
        )

    request = EmailAnalysisRequest(
        subject=subject,
        sender=sender,
        recipients=recipients or [],
        body=body,
        provider=provider,
        generate_reply=generate_reply,
        reply_style=ReplyStyle(
            reply_style
        ),
    )

    result = await analyze_email(
        request
    )

    return result.model_dump(
        mode="json"
    )
