from typing import Any

from app.services.notification_service import (
    list_notifications,
)
from app.services.task_service import (
    list_tasks,
)
from app.services.workflow_service import (
    list_executions,
)


_ALLOWED_OPERATIONS = {
    "list_tasks",
    "list_notifications",
    "list_workflow_executions",
}


async def call_internal_api(
    *,
    operation: str,
    unread_only: bool = False,
) -> dict[str, Any]:
    """
    Execute an allowlisted internal application operation.

    This intentionally calls local services directly instead of
    making an HTTP request back into the same FastAPI process.
    """

    normalized = operation.strip().lower()

    if normalized not in _ALLOWED_OPERATIONS:
        raise ValueError(
            "Unsupported internal_api operation. "
            f"Allowed operations: {sorted(_ALLOWED_OPERATIONS)}"
        )

    if normalized == "list_tasks":
        items = [
            item.model_dump(
                mode="json"
            )
            for item in list_tasks()
        ]

    elif normalized == "list_notifications":
        items = [
            item.model_dump(
                mode="json"
            )
            for item in list_notifications(
                unread_only=unread_only
            )
        ]

    else:
        items = [
            item.model_dump(
                mode="json"
            )
            for item in list_executions()
        ]

    return {
        "operation": normalized,
        "count": len(items),
        "items": items,
    }
