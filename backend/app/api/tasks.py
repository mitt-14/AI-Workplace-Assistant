from fastapi import APIRouter
from app.schemas.task import TaskListResponse,TaskResponse,TaskStatus,TaskUpdate
from app.services.task_service import get_task,list_tasks,update_task
router=APIRouter(prefix="/tasks",tags=["Tasks"])
@router.get("",response_model=TaskListResponse)
async def tasks(status:TaskStatus|None=None):
    items=list_tasks(status); return TaskListResponse(total=len(items),tasks=items)
@router.get("/{task_id}",response_model=TaskResponse)
async def task(task_id:str): return get_task(task_id)
@router.patch("/{task_id}",response_model=TaskResponse)
async def patch_task(task_id:str,request:TaskUpdate): return update_task(task_id,request)
