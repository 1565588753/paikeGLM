"""
学年管理 API 路由
- GET / - 学年列表
- POST / - 创建学年
- POST /{id}/switch - 切换学年
- GET /semesters - 学期列表 (通过查询参数)
- GET /grades - 年级列表 (通过查询参数)
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.services.academic_service import AcademicService, SemesterService, GradeService
from app.schemas.academic import (
    AcademicYearCreate, AcademicYearResponse,
    SemesterResponse, GradeCreate, GradeResponse, YearSwitchResponse,
)

router = APIRouter()


@router.get("", response_model=list[AcademicYearResponse], summary="获取学年列表")
def list_academic_years(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有学年列表"""
    return AcademicService.list_academic_years(db)


@router.post("", response_model=AcademicYearResponse, summary="创建学年")
def create_academic_year(
    data: AcademicYearCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    创建学年（仅管理员）

    - 自动创建上学期和下学期
    """
    result = AcademicService.create_academic_year(db, data)

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="academic_year",
        detail=f"创建学年 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/{year_id}/switch", response_model=YearSwitchResponse, summary="切换学年")
def switch_academic_year(
    year_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    切换到新学年（仅管理员）

    - 自动升级：高一->高二，高二->高三
    - 复制基础数据到新学年
    - 归档旧学年
    """
    result = AcademicService.switch_academic_year(db, year_id)

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="switch",
        target_type="academic_year",
        target_id=year_id,
        detail=result.message,
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.get("/semesters", response_model=list[SemesterResponse], summary="获取学期列表")
def list_semesters(
    academic_year_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取学期列表，可按学年筛选"""
    return SemesterService.list_semesters(db, academic_year_id)


@router.get("/grades", response_model=list[GradeResponse], summary="获取年级列表")
def list_grades(
    academic_year_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取年级列表，可按学年筛选"""
    return GradeService.list_grades(db, academic_year_id)


@router.post("/grades", response_model=GradeResponse, summary="创建年级")
def create_grade(
    data: GradeCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建年级（仅管理员）"""
    result = GradeService.create_grade(db, data)

    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="grade",
        detail=f"创建年级 {data.name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result
