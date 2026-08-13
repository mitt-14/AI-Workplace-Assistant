from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.tools.document_tool import (
    analyze_uploaded_document,
)
from app.agents.tools.email_tool import (
    analyze_email_with_agent,
)
from app.agents.tools.internal_api_tool import (
    call_internal_api,
)
from app.agents.tools.meeting_tool import (
    analyze_meeting_with_agent,
)
from app.agents.tools.python_tool import (
    run_python_utility,
)
from app.agents.tools.rag_tool import (
    search_company_documents,
)
from app.agents.tools.report_tool import (
    generate_report,
)
from app.agents.tools.workflow_tool import (
    run_agent_document_workflow,
    run_agent_email_workflow,
)
from app.schemas.agent import (
    AgentToolDescription,
    AgentToolName,
)


ToolCallable = Callable[
    ...,
    Awaitable[dict[str, Any]],
]


_TOOL_REGISTRY: dict[
    AgentToolName,
    ToolCallable,
] = {
    "search_company_documents": (
        search_company_documents
    ),
    "analyze_document": (
        analyze_uploaded_document
    ),
    "analyze_email": (
        analyze_email_with_agent
    ),
    "analyze_meeting": (
        analyze_meeting_with_agent
    ),
    "run_email_workflow": (
        run_agent_email_workflow
    ),
    "run_document_workflow": (
        run_agent_document_workflow
    ),
    "internal_api": (
        call_internal_api
    ),
    "python_utility": (
        run_python_utility
    ),
    "generate_report": (
        generate_report
    ),
}


_TOOL_DESCRIPTIONS = [
    AgentToolDescription(
        name="search_company_documents",
        description=(
            "Search indexed company documents using semantic retrieval."
        ),
        argument_example={
            "query": "remote work policy",
            "top_k": 5,
            "document_id": None,
        },
    ),
    AgentToolDescription(
        name="analyze_document",
        description=(
            "Run the Phase 8 document analyzer for an uploaded document."
        ),
        argument_example={
            "document_id": "uuid",
            "refresh": False,
        },
    ),
    AgentToolDescription(
        name="analyze_email",
        description=(
            "Run the Phase 9 email analyzer on supplied email content."
        ),
        argument_example={
            "subject": "Security report",
            "body": "Please send the report by Friday.",
            "generate_reply": False,
        },
    ),
    AgentToolDescription(
        name="analyze_meeting",
        description=(
            "Run the Phase 10 meeting analyzer on a transcript."
        ),
        argument_example={
            "title": "Weekly meeting",
            "transcript": "Alice: ...",
            "generate_follow_up_email": False,
        },
    ),
    AgentToolDescription(
        name="run_email_workflow",
        description=(
            "Run Phase 11 email-to-tasks automation and persist tasks."
        ),
        argument_example={
            "body": "Please prepare the report by Friday.",
        },
    ),
    AgentToolDescription(
        name="run_document_workflow",
        description=(
            "Run Phase 11 document-to-tasks automation and persist tasks."
        ),
        argument_example={
            "document_id": "uuid",
        },
    ),
    AgentToolDescription(
        name="internal_api",
        description=(
            "Read local tasks, notifications, or workflow execution history."
        ),
        argument_example={
            "operation": "list_tasks",
        },
    ),
    AgentToolDescription(
        name="python_utility",
        description=(
            "Run an allowlisted local Python utility such as calculator, "
            "mean, median, sort, unique, word_count, or json_pretty."
        ),
        argument_example={
            "operation": "calculator",
            "expression": "(25 * 12) / 4",
        },
    ),
    AgentToolDescription(
        name="generate_report",
        description=(
            "Generate a deterministic Markdown report from structured sections."
        ),
        argument_example={
            "title": "Security Report",
            "summary": "Summary text",
            "sections": [],
        },
    ),
]


def list_agent_tools() -> list[
    AgentToolDescription
]:
    return [
        item.model_copy(
            deep=True
        )
        for item in _TOOL_DESCRIPTIONS
    ]


async def execute_agent_tool(
    name: AgentToolName,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    tool = _TOOL_REGISTRY.get(
        name
    )

    if tool is None:
        raise ValueError(
            f"Unknown agent tool: {name}"
        )

    return await tool(
        **arguments
    )
