from datetime import datetime, timezone
from uuid import uuid4
from app.core.exceptions import TaskNotFoundError
from app.core.workflow_store import connection
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus, TaskUpdate

def _parse(row) -> TaskResponse:
    return TaskResponse.model_validate(dict(row))

def create_task(data: TaskCreate) -> TaskResponse:
    now = datetime.now(timezone.utc)
    result = TaskResponse(task_id=str(uuid4()), status=TaskStatus.pending, created_at=now, updated_at=now, **data.model_dump())
    with connection() as conn:
        conn.execute("INSERT INTO tasks(task_id,title,description,owner,deadline,priority,status,source_type,source_id,workflow_execution_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (result.task_id,result.title,result.description,result.owner,result.deadline,result.priority.value,result.status.value,result.source_type,result.source_id,result.workflow_execution_id,result.created_at.isoformat(),result.updated_at.isoformat()))
    return result

def list_tasks(status: TaskStatus | None = None) -> list[TaskResponse]:
    with connection() as conn:
        if status:
            rows=conn.execute("SELECT task_id,title,description,owner,deadline,priority,status,source_type,source_id,workflow_execution_id,created_at,updated_at FROM tasks WHERE status=? ORDER BY created_at DESC",(status.value,)).fetchall()
        else:
            rows=conn.execute("SELECT task_id,title,description,owner,deadline,priority,status,source_type,source_id,workflow_execution_id,created_at,updated_at FROM tasks ORDER BY created_at DESC").fetchall()
    return [_parse(r) for r in rows]

def get_task(task_id: str) -> TaskResponse:
    with connection() as conn:
        row=conn.execute("SELECT task_id,title,description,owner,deadline,priority,status,source_type,source_id,workflow_execution_id,created_at,updated_at FROM tasks WHERE task_id=?",(task_id,)).fetchone()
    if not row: raise TaskNotFoundError(task_id)
    return _parse(row)

def update_task(task_id: str, update: TaskUpdate) -> TaskResponse:
    current=get_task(task_id); data=current.model_dump(); changes=update.model_dump(exclude_none=True); data.update(changes); data['updated_at']=datetime.now(timezone.utc)
    result=TaskResponse.model_validate(data)
    with connection() as conn:
        conn.execute("UPDATE tasks SET title=?,description=?,owner=?,deadline=?,priority=?,status=?,updated_at=? WHERE task_id=?",(result.title,result.description,result.owner,result.deadline,result.priority.value,result.status.value,result.updated_at.isoformat(),task_id))
    return result
