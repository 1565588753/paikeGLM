"""
操作日志服务模块
"""
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.backup import OperationLog
from app.models.user import User
from app.schemas.backup import OperationLogResponse


class LogService:
    """操作日志服务"""

    @staticmethod
    def log_operation(
        db: Session,
        user_id: Optional[int],
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> OperationLog:
        """记录操作日志"""
        log = OperationLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def list_logs(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取操作日志列表"""
        query = db.query(OperationLog)

        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if action:
            query = query.filter(OperationLog.action == action)
        if target_type:
            query = query.filter(OperationLog.target_type == target_type)

        total = query.count()
        logs = query.order_by(OperationLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = []
        for log in logs:
            resp = OperationLogResponse.model_validate(log)
            if log.user:
                resp.username = log.user.username
                resp.real_name = log.user.real_name
            items.append(resp)

        return {"items": items, "total": total, "page": page, "page_size": page_size}
