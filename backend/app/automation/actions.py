from app.schemas.task import TaskCreate, TaskPriority, TaskResponse
from app.services.task_service import create_task

def _priority(value: object) -> TaskPriority:
    raw=getattr(value,'value',value)
    try: return TaskPriority(str(raw))
    except ValueError: return TaskPriority.medium

def store_email_tasks(tasks, execution_id: str, source_id: str|None) -> list[TaskResponse]:
    return [create_task(TaskCreate(title=t.task,owner=t.owner,deadline=t.deadline,priority=_priority(t.priority),source_type='email',source_id=source_id,workflow_execution_id=execution_id)) for t in tasks]

def store_document_tasks(items, execution_id: str, document_id: str) -> list[TaskResponse]:
    return [create_task(TaskCreate(title=i.task,owner=i.owner,deadline=i.deadline,priority=_priority(i.priority),source_type='document',source_id=document_id,workflow_execution_id=execution_id,description=(f"Source pages: {', '.join(map(str,i.page_numbers))}" if i.page_numbers else None))) for i in items]
