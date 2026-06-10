"""
科目管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.subject_service import SubjectService
from app.schemas.subject import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SubjectSubMappingCreate, SubjectSubMappingResponse,
)

router = APIRouter()


@router.get("", summary="获取科目列表")
def list_subjects(
    academic_year_id: Optional[int] = None,
    subject_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取科目列表，支持按学年、类型筛选"""
    return SubjectService.list_subjects(db, academic_year_id, subject_type, page, page_size)


@router.post("", response_model=SubjectResponse, summary="创建科目")
def create_subject(
    data: SubjectCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建科目（仅管理员）"""
    result = SubjectService.create_subject(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="subject",
        detail=f"创建科目 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.put("/{subject_id}", response_model=SubjectResponse, summary="更新科目")
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新科目信息（仅管理员）"""
    result = SubjectService.update_subject(db, subject_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="subject",
        target_id=subject_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.delete("/{subject_id}", summary="删除科目")
def delete_subject(
    subject_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除科目（仅管理员）"""
    SubjectService.delete_subject(db, subject_id)

    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        target_type="subject",
        target_id=subject_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": "删除成功"}
