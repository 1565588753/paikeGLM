"""
通知服务模块
- 通知的查询、标记已读
- 通知创建
- 未读数量统计
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse


class NotificationService:
    """通知管理服务"""

    @staticmethod
    def list_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationListResponse:
        """获取用户的通知列表"""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        total = query.count()
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

        notifications = query.order_by(Notification.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = [NotificationResponse.model_validate(n) for n in notifications]

        return NotificationListResponse(
            items=items,
            total=total,
            unread_count=unread_count,
        )

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> NotificationResponse:
        """标记通知为已读"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()
        if not notification:
            raise ValueError("通知不存在")

        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return NotificationResponse.model_validate(notification)

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """标记所有通知为已读"""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True})
        db.commit()
        return count

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        type: str,
        title: str,
        content: Optional[str] = None,
        related_id: Optional[int] = None,
    ) -> NotificationResponse:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            related_id=related_id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return NotificationResponse.model_validate(notification)
