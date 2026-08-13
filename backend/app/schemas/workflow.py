from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from app.schemas.email_analysis import EmailInput, ReplyStyle
from app.schemas.task import TaskResponse

class WorkflowType(str, Enum):
    email_to_tasks = "email_to_tasks"
    document_to_tasks = "document_to_tasks"

class WorkflowStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"

class EmailWorkflowRequest(EmailInput):
    provider: str | None = None
    generate_reply: bool = False
    reply_style: ReplyStyle = ReplyStyle.professional

class DocumentWorkflowRequest(BaseModel):
    document_id: str = Field(min_length=1)
    provider: str | None = None
    refresh_analysis: bool = False

class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    source_id: str | None = None
    provider: str | None = None
    created_task_count: int = 0
    tasks: list[TaskResponse] = Field(default_factory=list)
    notification_id: str | None = None
    analysis: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime
    completed_at: datetime | None = None

class WorkflowExecutionListResponse(BaseModel):
    total: int
    executions: list[WorkflowExecutionResponse] = Field(default_factory=list)
