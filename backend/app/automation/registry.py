from app.schemas.workflow import WorkflowType
WORKFLOW_DESCRIPTIONS={
 WorkflowType.email_to_tasks:"Analyze an email, extract tasks, store them, and notify the user.",
 WorkflowType.document_to_tasks:"Analyze an uploaded document, extract action items, store them, and notify the user.",
}
