from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentToolName = Literal[
    "search_company_documents",
    "analyze_document",
    "analyze_email",
    "analyze_meeting",
    "run_email_workflow",
    "run_document_workflow",
    "internal_api",
    "python_utility",
    "generate_report",
]


class AgentRequest(BaseModel):
    """
    Request for the local AI workplace agent.
    """

    instruction: str = Field(
        min_length=1,
        max_length=20_000,
    )

    provider: str | None = Field(
        default=None,
        examples=["ollama"],
    )

    max_steps: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Optional structured context such as document_id, "
            "email content, meeting transcript, or workflow inputs."
        ),
    )


class AgentPlanStep(BaseModel):
    step: int = Field(ge=1)
    tool: AgentToolName
    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )
    purpose: str = Field(
        min_length=1,
        max_length=500,
    )


class AgentPlan(BaseModel):
    goal: str
    steps: list[AgentPlanStep] = Field(
        default_factory=list,
    )


class AgentToolExecution(BaseModel):
    step: int
    tool: AgentToolName
    purpose: str
    status: Literal[
        "completed",
        "failed",
    ]
    result: Any | None = None
    error: str | None = None
    processing_time_seconds: float = 0.0


class AgentResponse(BaseModel):
    run_id: str
    instruction: str
    provider: str
    model: str | None = None
    plan_strategy: str
    plan: AgentPlan
    executions: list[AgentToolExecution] = Field(
        default_factory=list,
    )
    final_answer: str
    completed_steps: int
    failed_steps: int
    processing_time_seconds: float
    status: Literal[
        "completed",
        "partial",
        "failed",
    ]


class AgentToolDescription(BaseModel):
    name: AgentToolName
    description: str
    argument_example: dict[str, Any] = Field(
        default_factory=dict,
    )


class AgentToolListResponse(BaseModel):
    total: int
    tools: list[AgentToolDescription]
