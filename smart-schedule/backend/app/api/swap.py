"""
调课管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_user
from app.services.swap_service import SwapService
from app.schemas.swap import CourseSwapCreate, CourseSwapRespond, CourseSwapResponse

router = APIRouter()


@router.get("", summary="获取调课请求列表")
def list_swap_requests(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取调课请求列表

    - 管理员可查看所有请求
    - 教师只能查看自己相关的请求
    """
    user_id = None if current_user.role == "admin" else current_user.id
    return SwapService.list_swap_requests(db, user_id, status, page, page_size)


@router.post("", response_model=CourseSwapResponse, summary="创建调课请求")
def create_swap_request(
    data: CourseSwapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建调课请求

    - 请求者必须是其中一个条目的任课教师
    - 会自动发送通知给目标教师
    """
    return SwapService.create_swap_request(db, current_user.id, data)


@router.put("/{swap_id}/respond", response_model=CourseSwapResponse, summary="响应调课请求")
def respond_swap_request(
    swap_id: int,
    data: CourseSwapRespond,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    响应调课请求

    - 只有目标教师可以响应
    - 同意后会自动检查冲突并执行交换
    - 如果交换后产生冲突，会自动拒绝
    """
    return SwapService.respond_swap_request(db, swap_id, current_user.id, data)
