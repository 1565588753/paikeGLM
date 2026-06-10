"""
任课安排服务模块
- 任课安排的 CRUD
- 批量导入
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.timetable import TeachingAssignment
from app.models.user import User
from app.models.class_model import ClassGroup
from app.models.subject import Subject
from app.schemas.timetable import TeachingAssignmentCreate, TeachingAssignmentResponse


class TeachingService:
    """任课安排管理服务"""

    @staticmethod
    def list_teaching_assignments(
        db: Session,
        academic_year_id: Optional[int] = None,
        semester_id: Optional[int] = None,
        class_group_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取任课安排列表"""
        query = db.query(TeachingAssignment)

        if academic_year_id:
            query = query.filter(TeachingAssignment.academic_year_id == academic_year_id)
        if semester_id:
            query = query.filter(TeachingAssignment.semester_id == semester_id)
        if class_group_id:
            query = query.filter(TeachingAssignment.class_group_id == class_group_id)
        if teacher_id:
            query = query.filter(TeachingAssignment.teacher_id == teacher_id)
        if subject_id:
            query = query.filter(TeachingAssignment.subject_id == subject_id)

        total = query.count()
        assignments = query.offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for a in assignments:
            resp = TeachingAssignmentResponse.model_validate(a)
            if a.class_group:
                resp.class_name = a.class_group.name
            if a.subject:
                resp.subject_name = a.subject.name
            if a.teacher:
                resp.teacher_name = a.teacher.real_name
            items.append(resp)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create_teaching_assignment(db: Session, data: TeachingAssignmentCreate) -> TeachingAssignmentResponse:
        """创建任课安排"""
        # 检查是否已存在相同的安排
        existing = db.query(TeachingAssignment).filter(
            TeachingAssignment.class_group_id == data.class_group_id,
            TeachingAssignment.subject_id == data.subject_id,
            TeachingAssignment.academic_year_id == data.academic_year_id,
            TeachingAssignment.semester_id == data.semester_id,
        ).first()
        if existing:
            raise ValueError("该班级此科目已有任课安排")

        assignment = TeachingAssignment(**data.model_dump())
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        resp = TeachingAssignmentResponse.model_validate(assignment)
        if assignment.class_group:
            resp.class_name = assignment.class_group.name
        if assignment.subject:
            resp.subject_name = assignment.subject.name
        if assignment.teacher:
            resp.teacher_name = assignment.teacher.real_name
        return resp

    @staticmethod
    def delete_teaching_assignment(db: Session, assignment_id: int) -> bool:
        """删除任课安排"""
        assignment = db.query(TeachingAssignment).filter(TeachingAssignment.id == assignment_id).first()
        if not assignment:
            raise ValueError("任课安排不存在")

        db.delete(assignment)
        db.commit()
        return True

    @staticmethod
    def import_assignments(db: Session, data: TeachingAssignmentImport) -> dict:
        """批量导入任课安排"""
        success_count = 0
        fail_count = 0
        errors = []

        for i, item in enumerate(data.assignments):
            try:
                TeachingService.create_teaching_assignment(db, item)
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(f"第{i + 1}条: {str(e)}")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors,
        }
