"""
学年管理服务模块
- 学年/学期/年级的 CRUD
- 学年切换（自动升级逻辑）
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.academic import AcademicYear, Semester, Grade
from app.models.class_model import ClassGroup
from app.models.subject import Subject, SubjectSubMapping
from app.models.classroom import Classroom
from app.models.schedule import ScheduleTemplate
from app.models.timetable import TeachingAssignment, SchedulePlan
from app.models.staff import StaffTableEntry
from app.schemas.academic import (
    AcademicYearCreate, AcademicYearResponse,
    SemesterCreate, SemesterResponse,
    GradeCreate, GradeResponse, YearSwitchResponse,
)


class AcademicService:
    """学年管理服务"""

    # ==================== 学年管理 ====================

    @staticmethod
    def list_academic_years(db: Session) -> List[AcademicYearResponse]:
        """获取所有学年列表"""
        years = db.query(AcademicYear).order_by(AcademicYear.created_at.desc()).all()
        return [AcademicYearResponse.model_validate(y) for y in years]

    @staticmethod
    def create_academic_year(db: Session, data: AcademicYearCreate) -> AcademicYearResponse:
        """创建学年"""
        # 检查名称是否重复
        existing = db.query(AcademicYear).filter(AcademicYear.name == data.name).first()
        if existing:
            raise ValueError(f"学年 {data.name} 已存在")

        year = AcademicYear(name=data.name, status="pending", is_current=False)
        db.add(year)
        db.commit()
        db.refresh(year)

        # 自动创建两个学期
        for sem_name in ["上学期", "下学期"]:
            semester = Semester(
                academic_year_id=year.id,
                name=sem_name,
                is_current=False,
                status="pending",
            )
            db.add(semester)

        db.commit()
        return AcademicYearResponse.model_validate(year)

    @staticmethod
    def switch_academic_year(db: Session, new_year_id: int) -> YearSwitchResponse:
        """
        切换到新学年 - 核心业务逻辑

        自动升级流程：
        1. 将当前学年标记为 archived
        2. 将新学年标记为 active 和 is_current
        3. 从旧学年复制基础数据到新学年：
           - 年级（升级：高一->高二，高二->高三，高三毕业不复制）
           - 班级（跟随年级升级）
           - 科目（复制到新学年）
           - 教室（复制到新学年）
           - 作息时间模板（复制到新学年）
        4. 创建新学年的学期
        """
        # 获取当前学年
        current_year = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
        new_year = db.query(AcademicYear).filter(AcademicYear.id == new_year_id).first()

        if not new_year:
            raise ValueError("目标学年不存在")

        if new_year.is_current:
            raise ValueError("该学年已经是当前学年")

        old_year_id = current_year.id if current_year else 0

        # 1. 将当前学年归档
        if current_year:
            current_year.is_current = False
            current_year.status = "archived"
            # 归档当前学期的学期
            for sem in current_year.semesters:
                sem.is_current = False
                sem.status = "archived"

        # 2. 激活新学年
        new_year.is_current = True
        new_year.status = "active"

        # 激活第一个学期
        first_semester = db.query(Semester).filter(
            Semester.academic_year_id == new_year_id
        ).order_by(Semester.id).first()
        if first_semester:
            first_semester.is_current = True
            first_semester.status = "active"

        # 3. 从旧学年复制基础数据（如果存在旧学年）
        if current_year:
            _copy_data_to_new_year(db, old_year_id, new_year_id)

        db.commit()

        return YearSwitchResponse(
            message=f"已切换到学年 {new_year.name}",
            old_year_id=old_year_id,
            new_year_id=new_year_id,
        )


def _copy_data_to_new_year(db: Session, old_year_id: int, new_year_id: int):
    """
    从旧学年复制基础数据到新学年

    升级规则：
    - 高一(1) -> 高二(1)，高二(1) -> 高三(1)，高三不复制（毕业）
    - 科目、教室、作息模板直接复制
    """
    # 复制年级（升级）
    old_grades = db.query(Grade).filter(Grade.academic_year_id == old_year_id).all()
    grade_mapping = {}  # old_id -> new_id

    # 年级升级映射
    level_upgrade = {1: 2, 2: 3}  # 高一->高二, 高二->高三, 高三不升级
    name_upgrade = {"高一": "高二", "高二": "高三"}

    for old_grade in old_grades:
        # 高三毕业，不复制
        if old_grade.level >= 3:
            continue

        new_level = level_upgrade.get(old_grade.level, old_grade.level + 1)
        new_name = name_upgrade.get(old_grade.name, old_grade.name)

        # 检查新学年是否已有该年级
        existing = db.query(Grade).filter(
            Grade.academic_year_id == new_year_id,
            Grade.level == new_level,
        ).first()

        if not existing:
            new_grade = Grade(
                name=new_name,
                level=new_level,
                academic_year_id=new_year_id,
            )
            db.add(new_grade)
            db.flush()
            grade_mapping[old_grade.id] = new_grade.id

    # 复制班级（跟随年级升级）
    for old_grade in old_grades:
        if old_grade.id not in grade_mapping:
            continue

        new_grade_id = grade_mapping[old_grade.id]
        old_classes = db.query(ClassGroup).filter(
            ClassGroup.grade_id == old_grade.id
        ).all()

        for old_class in old_classes:
            # 班级名称升级：高一(1)班 -> 高二(1)班
            new_name = old_class.name.replace("高一", "高二").replace("高二", "高三")
            new_short_name = old_class.short_name  # 简称不变

            new_class = ClassGroup(
                name=new_name,
                short_name=new_short_name,
                grade_id=new_grade_id,
                student_count=0,  # 新学年学生数待更新
                head_teacher_id=old_class.head_teacher_id,
                class_type=old_class.class_type,
                academic_year_id=new_year_id,
            )
            db.add(new_class)

    # 复制科目
    old_subjects = db.query(Subject).filter(Subject.academic_year_id == old_year_id).all()
    for old_subject in old_subjects:
        existing = db.query(Subject).filter(
            Subject.academic_year_id == new_year_id,
            Subject.name == old_subject.name,
        ).first()
        if not existing:
            new_subject = Subject(
                name=old_subject.name,
                short_name=old_subject.short_name,
                subject_type=old_subject.subject_type,
                priority=old_subject.priority,
                allow_consecutive=old_subject.allow_consecutive,
                max_consecutive=old_subject.max_consecutive,
                needs_special_room=old_subject.needs_special_room,
                max_per_day=old_subject.max_per_day,
                max_per_week=old_subject.max_per_week,
                supports_odd_even=old_subject.supports_odd_even,
                academic_year_id=new_year_id,
            )
            db.add(new_subject)

    # 复制教室
    old_classrooms = db.query(Classroom).filter(Classroom.academic_year_id == old_year_id).all()
    for old_room in old_classrooms:
        existing = db.query(Classroom).filter(
            Classroom.academic_year_id == new_year_id,
            Classroom.name == old_room.name,
        ).first()
        if not existing:
            new_room = Classroom(
                name=old_room.name,
                room_type=old_room.room_type,
                capacity=old_room.capacity,
                location=old_room.location,
                equipment=old_room.equipment,
                academic_year_id=new_year_id,
            )
            db.add(new_room)

    # 复制作息时间模板
    old_templates = db.query(ScheduleTemplate).filter(
        ScheduleTemplate.academic_year_id == old_year_id
    ).all()
    for old_template in old_templates:
        # 查找新年级ID
        new_grade_id = None
        if old_template.grade_id and old_template.grade_id in grade_mapping:
            new_grade_id = grade_mapping[old_template.grade_id]

        new_template = ScheduleTemplate(
            name=old_template.name,
            grade_id=new_grade_id,
            academic_year_id=new_year_id,
            days_per_week=old_template.days_per_week,
            is_default=old_template.is_default,
        )
        db.add(new_template)
        db.flush()

        # 复制时间段
        for old_slot in old_template.time_slots:
            from app.models.schedule import TimeSlot
            new_slot = TimeSlot(
                schedule_template_id=new_template.id,
                day_of_week=old_slot.day_of_week,
                period_number=old_slot.period_number,
                start_time=old_slot.start_time,
                end_time=old_slot.end_time,
                period_type=old_slot.period_type,
                label=old_slot.label,
                is_morning=old_slot.is_morning,
                is_afternoon=old_slot.is_afternoon,
                is_evening=old_slot.is_evening,
            )
            db.add(new_slot)

    # 复制主科-小课映射
    old_mappings = db.query(SubjectSubMapping).filter(
        SubjectSubMapping.academic_year_id == old_year_id
    ).all()
    for old_mapping in old_mappings:
        new_mapping = SubjectSubMapping(
            subject_id=old_mapping.subject_id,  # 暂用旧ID，后续需要更新
            sub_subject_id=old_mapping.sub_subject_id,
            academic_year_id=new_year_id,
            enabled=old_mapping.enabled,
        )
        db.add(new_mapping)

    # 为新学年创建默认年级（高一新生）
    existing_grade_1 = db.query(Grade).filter(
        Grade.academic_year_id == new_year_id,
        Grade.level == 1,
    ).first()
    if not existing_grade_1:
        new_grade_1 = Grade(name="高一", level=1, academic_year_id=new_year_id)
        db.add(new_grade_1)


class SemesterService:
    """学期管理服务"""

    @staticmethod
    def list_semesters(db: Session, academic_year_id: Optional[int] = None) -> List[SemesterResponse]:
        """获取学期列表"""
        query = db.query(Semester)
        if academic_year_id:
            query = query.filter(Semester.academic_year_id == academic_year_id)
        semesters = query.order_by(Semester.id).all()
        return [SemesterResponse.model_validate(s) for s in semesters]


class GradeService:
    """年级管理服务"""

    @staticmethod
    def list_grades(db: Session, academic_year_id: Optional[int] = None) -> List[GradeResponse]:
        """获取年级列表"""
        query = db.query(Grade)
        if academic_year_id:
            query = query.filter(Grade.academic_year_id == academic_year_id)
        grades = query.order_by(Grade.level).all()
        return [GradeResponse.model_validate(g) for g in grades]

    @staticmethod
    def create_grade(db: Session, data: GradeCreate) -> GradeResponse:
        """创建年级"""
        grade = Grade(
            name=data.name,
            level=data.level,
            academic_year_id=data.academic_year_id,
        )
        db.add(grade)
        db.commit()
        db.refresh(grade)
        return GradeResponse.model_validate(grade)
