from datetime import datetime, timezone
from uuid import uuid4
from app.core.exceptions import NotificationNotFoundError
from app.core.workflow_store import connection
from app.schemas.notification import NotificationLevel, NotificationResponse

def create_notification(title: str, message: str, level: NotificationLevel=NotificationLevel.info, workflow_execution_id: str|None=None) -> NotificationResponse:
    item=NotificationResponse(notification_id=str(uuid4()),title=title,message=message,level=level,is_read=False,workflow_execution_id=workflow_execution_id,created_at=datetime.now(timezone.utc))
    with connection() as conn:
        conn.execute("INSERT INTO notifications VALUES (?,?,?,?,?,?,?)",(item.notification_id,item.title,item.message,item.level.value,0,item.workflow_execution_id,item.created_at.isoformat()))
    return item

def list_notifications(unread_only: bool=False) -> list[NotificationResponse]:
    with connection() as conn:
        sql="SELECT * FROM notifications" + (" WHERE is_read=0" if unread_only else "") + " ORDER BY created_at DESC"
        rows=conn.execute(sql).fetchall()
    return [NotificationResponse.model_validate({**dict(r),'is_read':bool(r['is_read'])}) for r in rows]

def mark_notification_read(notification_id: str) -> NotificationResponse:
    with connection() as conn:
        row=conn.execute("SELECT * FROM notifications WHERE notification_id=?",(notification_id,)).fetchone()
        if not row: raise NotificationNotFoundError(notification_id)
        conn.execute("UPDATE notifications SET is_read=1 WHERE notification_id=?",(notification_id,))
        data=dict(row); data['is_read']=True
    return NotificationResponse.model_validate(data)
