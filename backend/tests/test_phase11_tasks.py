import pytest
from app.core import workflow_store
from app.schemas.task import TaskCreate,TaskStatus,TaskUpdate
from app.services.task_service import create_task,get_task,update_task

@pytest.fixture(autouse=True)
def local_db(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_store.settings,'workflow_database_path',str(tmp_path/'workflows.db'))
    workflow_store.initialize_workflow_database()

def test_task_lifecycle():
    task=create_task(TaskCreate(title='Prepare report'))
    assert get_task(task.task_id).status==TaskStatus.pending
    updated=update_task(task.task_id,TaskUpdate(status=TaskStatus.completed))
    assert updated.status==TaskStatus.completed
