"""
人事表管理 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.staff_service import StaffService
from app.schemas.staff import StaffEntryUpdate, StaffEntryResponse

router = APIRouter()


@router.get("", summary="获取人事表条目列表")
def list_staff_entries(
    academic_year_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    class_group_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取人事表条目列表，支持多种筛选条件"""
    return StaffService.list_staff_entries(
        db, academic_year_id, semester_id, grade_id,
        class_group_id, subject_id, teacher_id, page, page_size,
    )


@router.put("/{entry_id}", response_model=StaffEntryResponse, summary="更新人事表条目")
def update_staff_entry(
    entry_id: int,
    data: StaffEntryUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新人事表条目（仅管理员）"""
    result = StaffService.update_staff_entry(db, entry_id, data)

    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="staff_entry",
        target_id=entry_id,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/import", summary="导入人事表")
def import_staff_entries(
    data: dict,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    批量导入人事表（仅管理员）

    请求体格式: {"entries": [{...}, {...}]}
    """
    entries = data.get("entries", [])
    result = StaffService.import_staff_entries(db, entries)

    log = OperationLog(
        user_id=current_user.id,
        action="import",
        target_type="staff_entry",
        detail=f"导入人事表: 成功{result['success_count']}条",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/sync", summary="从任课安排同步人事表")
def sync_staff_from_teaching(
    academic_year_id: int,
    semester_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    从任课安排同步人事表（仅管理员）

    - 清除旧数据后重新生成
    """
    count = StaffService.sync_from_teaching_assignments(db, academic_year_id, semester_id)

    log = OperationLog(
        user_id=current_user.id,
        action="sync",
        target_type="staff_entry",
        detail=f"同步人事表: 生成{count}条",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": f"同步完成，生成 {count} 条记录"}
