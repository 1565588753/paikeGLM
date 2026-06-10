"""
教室管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.classroom_service import ClassroomService
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse

router = APIRouter()


@router.get("", summary="获取教室列表")
def list_classrooms(
    academic_year_id: Optional[int] = None,
    room_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取教室列表，支持按学年、类型筛选"""
    return ClassroomService.list_classrooms(db, academic_year_id, room_type, page, page_size)


@router.post("", response_model=ClassroomResponse, summary="创建教室")
def create_classroom(
    data: ClassroomCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建教室（仅管理员）"""
    result = ClassroomService.create_classroom(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="classroom",
        detail=f"创建教室 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.put("/{classroom_id}", response_model=ClassroomResponse, summary="更新教室")
def update_classroom(
    classroom_id: int,
    data: ClassroomUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新教室信息（仅管理员）"""
    result = ClassroomService.update_classroom(db, classroom_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="classroom",
        target_id=classroom_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.delete("/{classroom_id}", summary="删除教室")
def delete_classroom(
    classroom_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除教室（仅管理员）"""
    ClassroomService.delete_classroom(db, classroom_id)

    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        target_type="classroom",
        target_id=classroom_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": "删除成功"}
