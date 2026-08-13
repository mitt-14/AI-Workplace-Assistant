from datetime import datetime, timezone
from uuid import uuid4
from app.automation.actions import store_document_tasks, store_email_tasks
from app.core.workflow_store import connection, encode_json
from app.schemas.email_analysis import EmailAnalysisRequest
from app.schemas.notification import NotificationLevel
from app.schemas.workflow import DocumentWorkflowRequest, EmailWorkflowRequest, WorkflowExecutionResponse, WorkflowStatus, WorkflowType
from app.services.document_analyzer import analyze_document
from app.services.email_analyzer import analyze_email
from app.services.notification_service import create_notification
from app.services.task_service import list_tasks

def _start(kind, source_id, provider):
    eid=str(uuid4()); started=datetime.now(timezone.utc)
    with connection() as conn: conn.execute("INSERT INTO workflow_executions(execution_id,workflow_type,status,source_id,provider,started_at) VALUES(?,?,?,?,?,?)",(eid,kind.value,WorkflowStatus.running.value,source_id,provider,started.isoformat()))
    return eid,started

def _finish(eid,status,analysis=None,error=None):
    completed=datetime.now(timezone.utc)
    with connection() as conn: conn.execute("UPDATE workflow_executions SET status=?,analysis_json=?,error=?,completed_at=? WHERE execution_id=?",(status.value,encode_json(analysis) if analysis is not None else None,error,completed.isoformat(),eid))
    return completed

async def run_email_workflow(request: EmailWorkflowRequest) -> WorkflowExecutionResponse:
    source_id=request.sender or request.subject; provider=request.provider
    eid,started=_start(WorkflowType.email_to_tasks,source_id,provider)
    try:
        analysis=await analyze_email(EmailAnalysisRequest(**request.model_dump()))
        tasks=store_email_tasks(analysis.tasks,eid,source_id)
        note=create_notification("Email workflow completed",f"Email analyzed successfully. {len(tasks)} task(s) created.",NotificationLevel.success,eid)
        completed=_finish(eid,WorkflowStatus.completed,analysis.model_dump(mode='json'))
        return WorkflowExecutionResponse(execution_id=eid,workflow_type=WorkflowType.email_to_tasks,status=WorkflowStatus.completed,source_id=source_id,provider=analysis.provider,created_task_count=len(tasks),tasks=tasks,notification_id=note.notification_id,analysis=analysis.model_dump(mode='json'),started_at=started,completed_at=completed)
    except Exception as exc:
        _finish(eid,WorkflowStatus.failed,error=str(exc)); create_notification("Email workflow failed",str(exc),NotificationLevel.error,eid); raise

async def run_document_workflow(request: DocumentWorkflowRequest) -> WorkflowExecutionResponse:
    eid,started=_start(WorkflowType.document_to_tasks,request.document_id,request.provider)
    try:
        analysis=await analyze_document(document_id=request.document_id,provider=request.provider,refresh=request.refresh_analysis)
        tasks=store_document_tasks(analysis.action_items,eid,request.document_id)
        note=create_notification("Document workflow completed",f"Document analyzed successfully. {len(tasks)} task(s) created.",NotificationLevel.success,eid)
        completed=_finish(eid,WorkflowStatus.completed,analysis.model_dump(mode='json'))
        return WorkflowExecutionResponse(execution_id=eid,workflow_type=WorkflowType.document_to_tasks,status=WorkflowStatus.completed,source_id=request.document_id,provider=analysis.provider,created_task_count=len(tasks),tasks=tasks,notification_id=note.notification_id,analysis=analysis.model_dump(mode='json'),started_at=started,completed_at=completed)
    except Exception as exc:
        _finish(eid,WorkflowStatus.failed,error=str(exc)); create_notification("Document workflow failed",str(exc),NotificationLevel.error,eid); raise

def list_executions() -> list[WorkflowExecutionResponse]:
    import json
    with connection() as conn: rows=conn.execute("SELECT * FROM workflow_executions ORDER BY started_at DESC").fetchall()
    out=[]
    for r in rows:
        tasks=[t for t in list_tasks() if t.workflow_execution_id==r['execution_id']]
        out.append(WorkflowExecutionResponse(execution_id=r['execution_id'],workflow_type=r['workflow_type'],status=r['status'],source_id=r['source_id'],provider=r['provider'],created_task_count=len(tasks),tasks=tasks,analysis=json.loads(r['analysis_json']) if r['analysis_json'] else None,error=r['error'],started_at=r['started_at'],completed_at=r['completed_at']))
    return out
