from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from app.core import workflow_store
from app.schemas.workflow import EmailWorkflowRequest, DocumentWorkflowRequest
from app.services import workflow_service

@pytest.fixture(autouse=True)
def local_db(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_store.settings, 'workflow_database_path', str(tmp_path/'workflows.db'))
    workflow_store.initialize_workflow_database()

def test_email_workflow_creates_task(monkeypatch):
    analysis=SimpleNamespace(provider='ollama',tasks=[SimpleNamespace(task='Send report',owner='Miten',deadline='Friday',priority='high')],model_dump=lambda mode=None:{'provider':'ollama','tasks':[]})
    monkeypatch.setattr(workflow_service,'analyze_email',AsyncMock(return_value=analysis))
    result=__import__('asyncio').run(workflow_service.run_email_workflow(EmailWorkflowRequest(subject='Report',body='Send report Friday',provider='ollama')))
    assert result.status.value=='completed'
    assert result.created_task_count==1
    assert result.tasks[0].title=='Send report'

def test_document_workflow_creates_task(monkeypatch):
    analysis=SimpleNamespace(provider='ollama',action_items=[SimpleNamespace(task='Review contract',owner=None,deadline='Monday',priority='medium',page_numbers=[2])],model_dump=lambda mode=None:{'provider':'ollama','action_items':[]})
    monkeypatch.setattr(workflow_service,'analyze_document',AsyncMock(return_value=analysis))
    result=__import__('asyncio').run(workflow_service.run_document_workflow(DocumentWorkflowRequest(document_id='doc-1',provider='ollama')))
    assert result.status.value=='completed'
    assert result.created_task_count==1
    assert result.tasks[0].source_type=='document'
