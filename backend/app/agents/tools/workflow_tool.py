from typing import Any

from app.schemas.email_analysis import ReplyStyle
from app.schemas.workflow import (
    DocumentWorkflowRequest,
    EmailWorkflowRequest,
)
from app.services.workflow_service import (
    run_document_workflow,
    run_email_workflow,
)


async def run_agent_email_workflow(
    *,
    body: str,
    provider: str | None = None,
    subject: str | None = None,
    sender: str | None = None,
    recipients: list[str] | None = None,
    generate_reply: bool = False,
    reply_style: str = "professional",
) -> dict[str, Any]:
    request = EmailWorkflowRequest(
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

    result = await run_email_workflow(
        request
    )

    return result.model_dump(
        mode="json"
    )


async def run_agent_document_workflow(
    *,
    document_id: str,
    provider: str | None = None,
    refresh_analysis: bool = False,
) -> dict[str, Any]:
    request = DocumentWorkflowRequest(
        document_id=document_id,
        provider=provider,
        refresh_analysis=refresh_analysis,
    )

    result = await run_document_workflow(
        request
    )

    return result.model_dump(
        mode="json"
    )
