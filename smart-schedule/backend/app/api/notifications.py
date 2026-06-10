"""
通知管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse, NotificationListResponse

router = APIRouter()


@router.get("", response_model=NotificationListResponse, summary="获取通知列表")
def list_notifications(
    is_read: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的通知列表

    - 支持按已读/未读筛选
    - 返回未读数量
    """
    return NotificationService.list_notifications(
        db, current_user.id, is_read, page, page_size,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="标记通知已读")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记指定通知为已读"""
    return NotificationService.mark_as_read(db, notification_id, current_user.id)


@router.put("/read-all", summary="标记所有通知已读")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记当前用户的所有通知为已读"""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": f"已标记 {count} 条通知为已读"}
