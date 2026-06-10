"""
作息时间模板管理 API 路由
- 作息时间模板 CRUD
- 时间段管理
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import (
    ScheduleTemplateCreate, ScheduleTemplateResponse,
    TimeSlotBatchUpdate, TimeSlotResponse,
)

router = APIRouter()


@router.get("/templates", response_model=list[ScheduleTemplateResponse], summary="获取作息时间模板列表")
def list_templates(
    academic_year_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取作息时间模板列表"""
    return ScheduleService.list_templates(db, academic_year_id)


@router.post("/templates", response_model=ScheduleTemplateResponse, summary="创建作息时间模板")
def create_template(
    data: ScheduleTemplateCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建作息时间模板（仅管理员）"""
    result = ScheduleService.create_template(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="schedule_template",
        detail=f"创建作息时间模板 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.get("/templates/{template_id}/slots", response_model=list[TimeSlotResponse], summary="获取模板的时间段")
def get_template_slots(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定模板的时间段列表"""
    return ScheduleService.get_template_slots(db, template_id)


@router.post("/templates/{template_id}/slots", response_model=list[TimeSlotResponse], summary="创建/更新时间段")
def update_template_slots(
    template_id: int,
    data: TimeSlotBatchUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    批量创建/更新时间段（仅管理员）

    - 先删除旧的时间段，再创建新的
    - 适合前端一次性提交整个模板的时间段
    """
    result = ScheduleService.update_template_slots(db, template_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="schedule_template",
        target_id=template_id,
        detail=f"更新模板 {template_id} 的时间段",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result
