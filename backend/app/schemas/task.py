from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    description: str | None = None
    owner: str | None = None
    deadline: str | None = None
    priority: TaskPriority = TaskPriority.medium
    source_type: str | None = None
    source_id: str | None = None
    workflow_execution_id: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=1000)
    description: str | None = None
    owner: str | None = None
    deadline: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None

class TaskResponse(TaskCreate):
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

class TaskListResponse(BaseModel):
    total: int
    tasks: list[TaskResponse] = Field(default_factory=list)
