"""
班级管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.class_service import ClassService
from app.schemas.class_model import ClassGroupCreate, ClassGroupUpdate, ClassGroupResponse, ClassGroupImport

router = APIRouter()


@router.get("", summary="获取班级列表")
def list_classes(
    academic_year_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取班级列表，支持按学年、年级筛选和分页"""
    return ClassService.list_classes(db, academic_year_id, grade_id, page, page_size)


@router.post("", response_model=ClassGroupResponse, summary="创建班级")
def create_class(
    data: ClassGroupCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建班级（仅管理员）"""
    result = ClassService.create_class(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="class",
        detail=f"创建班级 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.put("/{class_id}", response_model=ClassGroupResponse, summary="更新班级")
def update_class(
    class_id: int,
    data: ClassGroupUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新班级信息（仅管理员）"""
    result = ClassService.update_class(db, class_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="class",
        target_id=class_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.delete("/{class_id}", summary="删除班级")
def delete_class(
    class_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除班级（仅管理员）"""
    ClassService.delete_class(db, class_id)

    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        target_type="class",
        target_id=class_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": "删除成功"}


@router.post("/import", summary="批量导入班级")
def import_classes(
    data: ClassGroupImport,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """批量导入班级（仅管理员）"""
    result = ClassService.import_classes(db, data.classes)

    log = OperationLog(
        user_id=current_user.id,
        action="import",
        target_type="class",
        detail=f"批量导入班级: 成功{result['success_count']}个",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result
