from fastapi import APIRouter
from app.schemas.workflow import DocumentWorkflowRequest,EmailWorkflowRequest,WorkflowExecutionListResponse,WorkflowExecutionResponse
from app.services.workflow_service import list_executions,run_document_workflow,run_email_workflow
router=APIRouter(prefix="/workflows",tags=["Workflow Automation"])
@router.post("/email/run",response_model=WorkflowExecutionResponse)
async def email_workflow(request:EmailWorkflowRequest): return await run_email_workflow(request)
@router.post("/document/run",response_model=WorkflowExecutionResponse)
async def document_workflow(request:DocumentWorkflowRequest): return await run_document_workflow(request)
@router.get("/executions",response_model=WorkflowExecutionListResponse)
async def executions():
    items=list_executions(); return WorkflowExecutionListResponse(total=len(items),executions=items)
