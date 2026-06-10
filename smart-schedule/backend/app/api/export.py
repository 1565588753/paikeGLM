"""
导出导入 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_user, get_current_admin
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/timetable", summary="导出课表到Excel")
def export_timetable(
    plan_id: int,
    class_group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导出课表到 Excel 文件

    - 支持按班级或教师导出
    - 返回 .xlsx 文件下载
    """
    excel_bytes = ExportService.export_timetable(db, plan_id, class_group_id, teacher_id)

    # 确定文件名
    filename = "课表.xlsx"
    if class_group_id:
        filename = f"班级课表_{class_group_id}.xlsx"
    elif teacher_id:
        filename = f"教师课表_{teacher_id}.xlsx"

    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/staff", summary="导出人事表到Excel")
def export_staff_table(
    academic_year_id: int,
    semester_id: int,
    grade_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导出人事表到 Excel 文件

    - 按年级-班级-科目-教师矩阵展示
    - 返回 .xlsx 文件下载
    """
    excel_bytes = ExportService.export_staff_table(
        db, academic_year_id, semester_id, grade_id,
    )

    filename = f"人事表_{academic_year_id}.xlsx"

    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
