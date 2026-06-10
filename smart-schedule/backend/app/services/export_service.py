"""
导出导入服务模块
- 课表导出为 Excel
- 人事表导出为 Excel
- 数据导入
"""
import io
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.timetable import TimetableEntry, SchedulePlan
from app.models.staff import StaffTableEntry
from app.utils.excel_helper import (
    export_timetable_to_excel, export_staff_to_excel,
    read_excel_file, workbook_to_bytes,
)


class ExportService:
    """导出导入服务"""

    @staticmethod
    def export_timetable(
        db: Session,
        plan_id: int,
        class_group_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
    ) -> bytes:
        """
        导出课表到 Excel

        支持按班级或教师导出
        """
        query = db.query(TimetableEntry).filter(TimetableEntry.schedule_plan_id == plan_id)

        if class_group_id:
            query = query.filter(TimetableEntry.class_group_id == class_group_id)
        if teacher_id:
            query = query.filter(TimetableEntry.teacher_id == teacher_id)

        entries = query.order_by(TimetableEntry.day_of_week, TimetableEntry.period_number).all()

        # 转换为字典列表
        entry_dicts = []
        for e in entries:
            entry_dicts.append({
                "day_of_week": e.day_of_week,
                "period_number": e.period_number,
                "subject_name": e.subject.name if e.subject else "",
                "subject_short_name": e.subject.short_name if e.subject else "",
                "teacher_name": e.teacher.real_name if e.teacher else "",
                "classroom_name": e.classroom.name if e.classroom else "",
                "class_name": e.class_group.name if e.class_group else "",
                "odd_even_type": e.odd_even_type,
            })

        # 确定标题
        if class_group_id:
            class_entry = entries[0] if entries else None
            title = f"{class_entry.class_group.name}课表" if class_entry and class_entry.class_group else "课表"
        elif teacher_id:
            teacher_entry = entries[0] if entries else None
            title = f"{teacher_entry.teacher.real_name}课表" if teacher_entry and teacher_entry.teacher else "课表"
        else:
            plan = db.query(SchedulePlan).filter(SchedulePlan.id == plan_id).first()
            title = f"{plan.name}课表" if plan else "课表"

        # 计算最大节次
        max_period = max((e.period_number for e in entries), default=8)

        return export_timetable_to_excel(
            entries=entry_dicts,
            days_per_week=5,
            max_period=max_period,
            title=title,
        )

    @staticmethod
    def export_staff_table(
        db: Session,
        academic_year_id: int,
        semester_id: int,
        grade_id: Optional[int] = None,
    ) -> bytes:
        """导出人事表到 Excel"""
        query = db.query(StaffTableEntry).filter(
            StaffTableEntry.academic_year_id == academic_year_id,
            StaffTableEntry.semester_id == semester_id,
        )

        if grade_id:
            query = query.filter(StaffTableEntry.grade_id == grade_id)

        entries = query.all()

        # 转换为字典列表
        staff_data = []
        class_names = []
        subject_names = []

        for e in entries:
            staff_data.append({
                "subject_name": e.subject.name if e.subject else "",
                "class_name": e.class_group.name if e.class_group else "",
                "teacher_name": e.teacher.real_name if e.teacher else "",
            })
            if e.class_group and e.class_group.name not in class_names:
                class_names.append(e.class_group.name)
            if e.subject and e.subject.name not in subject_names:
                subject_names.append(e.subject.name)

        return export_staff_to_excel(
            staff_data=staff_data,
            class_names=sorted(class_names),
            subject_names=subject_names,
        )
