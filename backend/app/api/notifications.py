from fastapi import APIRouter
from app.schemas.notification import NotificationListResponse,NotificationResponse
from app.services.notification_service import list_notifications,mark_notification_read
router=APIRouter(prefix="/notifications",tags=["Notifications"])
@router.get("",response_model=NotificationListResponse)
async def notifications(unread_only:bool=False):
    items=list_notifications(unread_only); return NotificationListResponse(total=len(items),notifications=items)
@router.patch("/{notification_id}/read",response_model=NotificationResponse)
async def read_notification(notification_id:str): return mark_notification_read(notification_id)
