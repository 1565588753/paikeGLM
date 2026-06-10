"""
人事表服务模块
- 人事表的查询、更新、导入
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.staff import StaffTableEntry
from app.models.user import User
from app.models.class_model import ClassGroup
from app.models.subject import Subject
from app.models.academic import Grade
from app.schemas.staff import StaffEntryUpdate, StaffEntryResponse


class StaffService:
    """人事表管理服务"""

    @staticmethod
    def list_staff_entries(
        db: Session,
        academic_year_id: Optional[int] = None,
        semester_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        class_group_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """获取人事表条目列表"""
        query = db.query(StaffTableEntry)

        if academic_year_id:
            query = query.filter(StaffTableEntry.academic_year_id == academic_year_id)
        if semester_id:
            query = query.filter(StaffTableEntry.semester_id == semester_id)
        if grade_id:
            query = query.filter(StaffTableEntry.grade_id == grade_id)
        if class_group_id:
            query = query.filter(StaffTableEntry.class_group_id == class_group_id)
        if subject_id:
            query = query.filter(StaffTableEntry.subject_id == subject_id)
        if teacher_id:
            query = query.filter(StaffTableEntry.teacher_id == teacher_id)

        total = query.count()
        entries = query.offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for e in entries:
            resp = StaffEntryResponse.model_validate(e)
            if e.grade:
                resp.grade_name = e.grade.name
            if e.class_group:
                resp.class_name = e.class_group.name
            if e.subject:
                resp.subject_name = e.subject.name
            if e.teacher:
                resp.teacher_name = e.teacher.real_name
            items.append(resp)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def update_staff_entry(
        db: Session, entry_id: int, data: StaffEntryUpdate
    ) -> StaffEntryResponse:
        """更新人事表条目"""
        entry = db.query(StaffTableEntry).filter(StaffTableEntry.id == entry_id).first()
        if not entry:
            raise ValueError("人事表条目不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entry, key, value)

        db.commit()
        db.refresh(entry)

        resp = StaffEntryResponse.model_validate(entry)
        if entry.grade:
            resp.grade_name = entry.grade.name
        if entry.class_group:
            resp.class_name = entry.class_group.name
        if entry.subject:
            resp.subject_name = entry.subject.name
        if entry.teacher:
            resp.teacher_name = entry.teacher.real_name
        return resp

    @staticmethod
    def import_staff_entries(db: Session, entries_data: List[dict]) -> dict:
        """批量导入人事表"""
        success_count = 0
        fail_count = 0
        errors = []

        for i, data in enumerate(entries_data):
            try:
                entry = StaffTableEntry(**data)
                db.add(entry)
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(f"第{i + 1}条: {str(e)}")

        db.commit()
        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors,
        }

    @staticmethod
    def sync_from_teaching_assignments(
        db: Session, academic_year_id: int, semester_id: int
    ) -> int:
        """
        从任课安排同步人事表

        当任课安排更新后，调用此方法同步人事表数据
        """
        from app.models.timetable import TeachingAssignment

        # 清除旧数据
        db.query(StaffTableEntry).filter(
            StaffTableEntry.academic_year_id == academic_year_id,
            StaffTableEntry.semester_id == semester_id,
        ).delete()

        # 从任课安排生成
        assignments = db.query(TeachingAssignment).filter(
            TeachingAssignment.academic_year_id == academic_year_id,
            TeachingAssignment.semester_id == semester_id,
        ).all()

        count = 0
        for a in assignments:
            # 获取班级的年级
            class_group = db.query(ClassGroup).filter(ClassGroup.id == a.class_group_id).first()
            if not class_group:
                continue

            entry = StaffTableEntry(
                grade_id=class_group.grade_id,
                class_group_id=a.class_group_id,
                subject_id=a.subject_id,
                teacher_id=a.teacher_id,
                weekly_hours=a.weekly_hours,
                odd_even_type=a.odd_even_type,
                notes=a.notes,
                academic_year_id=a.academic_year_id,
                semester_id=a.semester_id,
            )
            db.add(entry)
            count += 1

        db.commit()
        return count
