from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class NotificationLevel(str, Enum):
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"

class NotificationResponse(BaseModel):
    notification_id: str
    title: str
    message: str
    level: NotificationLevel
    is_read: bool
    workflow_execution_id: str | None = None
    created_at: datetime

class NotificationListResponse(BaseModel):
    total: int
    notifications: list[NotificationResponse] = Field(default_factory=list)
