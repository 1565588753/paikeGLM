"""
操作日志 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_admin
from app.services.log_service import LogService

router = APIRouter()


@router.get("", summary="获取操作日志列表")
def list_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    获取操作日志列表（仅管理员）

    - 支持按用户、操作类型、目标类型筛选
    - 支持分页
    """
    return LogService.list_logs(db, user_id, action, target_type, page, page_size)
