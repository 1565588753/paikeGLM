"""
课表管理 API 路由 (挂载在 /api/timetables)
- 课表条目查询
- 自动排课
- 课表条目移动（拖拽）
- 冲突检查
- 排课方案管理
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.schedule_service import TimetableService, SchedulePlanService
from app.schemas.timetable import (
    TimetableMoveRequest, ConflictCheckRequest, ConflictCheckResponse,
    GenerateScheduleRequest, GenerateScheduleResponse,
    SchedulePlanCreate, SchedulePlanResponse,
)

router = APIRouter()


# ==================== 课表条目 ====================

@router.get("", summary="获取课表条目")
def get_timetable_entries(
    plan_id: Optional[int] = None,
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    odd_even: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取课表条目

    支持按方案、班级、教师、教室、单双周筛选
    """
    return TimetableService.get_timetable_entries(
        db, plan_id, class_id, teacher_id, classroom_id, odd_even,
    )


@router.post("/generate", response_model=GenerateScheduleResponse, summary="自动排课")
def generate_schedule(
    data: GenerateScheduleRequest,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    执行自动排课（仅管理员）

    - 基于约束满足算法
    - 支持预排课程
    - 自动冲突检测
    """
    result = TimetableService.generate_schedule(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="generate",
        target_type="timetable",
        target_id=data.plan_id,
        detail=f"自动排课: {result.message}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.put("/{entry_id}/move", summary="移动课表条目")
def move_timetable_entry(
    entry_id: int,
    data: TimetableMoveRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    移动课表条目（拖拽操作）

    - 自动检查冲突
    - 锁定的条目不可移动
    """
    result = TimetableService.move_entry(db, entry_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="move",
        target_type="timetable_entry",
        target_id=entry_id,
        detail=f"移动课表条目到 星期{data.day_of_week}第{data.period_number}节",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/check-conflict", response_model=ConflictCheckResponse, summary="检查冲突")
def check_conflict(
    data: ConflictCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    检查移动课表条目是否会产生冲突

    - 不实际执行移动
    - 返回冲突详情
    """
    return TimetableService.check_conflict(db, data)


# ==================== 排课方案 ====================

@router.get("/plans", response_model=list[SchedulePlanResponse], summary="获取排课方案列表")
def list_schedule_plans(
    academic_year_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取排课方案列表"""
    return SchedulePlanService.list_plans(db, academic_year_id)


@router.post("/plans", response_model=SchedulePlanResponse, summary="创建排课方案")
def create_schedule_plan(
    data: SchedulePlanCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建排课方案（仅管理员）"""
    result = SchedulePlanService.create_plan(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="schedule_plan",
        detail=f"创建排课方案 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/plans/{plan_id}/publish", response_model=SchedulePlanResponse, summary="发布排课方案")
def publish_schedule_plan(
    plan_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    发布排课方案（仅管理员）

    - 发布后其他方案取消激活
    - 该方案设为当前激活方案
    """
    result = SchedulePlanService.publish_plan(db, plan_id)

    log = OperationLog(
        user_id=current_user.id,
        action="publish",
        target_type="schedule_plan",
        target_id=plan_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result
