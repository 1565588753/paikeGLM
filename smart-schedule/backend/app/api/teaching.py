"""
任课安排 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.teaching_service import TeachingService
from app.schemas.timetable import TeachingAssignmentCreate, TeachingAssignmentResponse, TeachingAssignmentImport

router = APIRouter()


@router.get("", summary="获取任课安排列表")
def list_teaching_assignments(
    academic_year_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    class_group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取任课安排列表，支持多种筛选条件"""
    return TeachingService.list_teaching_assignments(
        db, academic_year_id, semester_id, class_group_id,
        teacher_id, subject_id, page, page_size,
    )


@router.post("", response_model=TeachingAssignmentResponse, summary="创建任课安排")
def create_teaching_assignment(
    data: TeachingAssignmentCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建任课安排（仅管理员）"""
    result = TeachingService.create_teaching_assignment(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="teaching_assignment",
        detail=f"创建任课安排: 班级{data.class_group_id} 科目{data.subject_id} 教师{data.teacher_id}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.delete("/{assignment_id}", summary="删除任课安排")
def delete_teaching_assignment(
    assignment_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除任课安排（仅管理员）"""
    TeachingService.delete_teaching_assignment(db, assignment_id)

    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        target_type="teaching_assignment",
        target_id=assignment_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": "删除成功"}


@router.post("/import", summary="批量导入任课安排")
def import_teaching_assignments(
    data: TeachingAssignmentImport,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """批量导入任课安排（仅管理员）"""
    result = TeachingService.import_assignments(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="import",
        target_type="teaching_assignment",
        detail=f"批量导入任课安排: 成功{result['success_count']}个",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result
