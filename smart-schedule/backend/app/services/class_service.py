"""
班级管理服务模块
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.class_model import ClassGroup
from app.models.user import User
from app.schemas.class_model import ClassGroupCreate, ClassGroupUpdate, ClassGroupResponse


class ClassService:
    """班级管理服务"""

    @staticmethod
    def list_classes(
        db: Session,
        academic_year_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取班级列表（分页）"""
        query = db.query(ClassGroup)

        if academic_year_id:
            query = query.filter(ClassGroup.academic_year_id == academic_year_id)
        if grade_id:
            query = query.filter(ClassGroup.grade_id == grade_id)

        total = query.count()
        classes = query.offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for c in classes:
            resp = ClassGroupResponse.model_validate(c)
            # 填充关联信息
            if c.grade:
                resp.grade_name = c.grade.name
            if c.head_teacher:
                resp.head_teacher_name = c.head_teacher.real_name
            items.append(resp)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create_class(db: Session, data: ClassGroupCreate) -> ClassGroupResponse:
        """创建班级"""
        # 检查班级名称是否重复
        existing = db.query(ClassGroup).filter(
            ClassGroup.name == data.name,
            ClassGroup.academic_year_id == data.academic_year_id,
        ).first()
        if existing:
            raise ValueError(f"班级 {data.name} 已存在")

        class_group = ClassGroup(
            name=data.name,
            short_name=data.short_name,
            grade_id=data.grade_id,
            student_count=data.student_count,
            head_teacher_id=data.head_teacher_id,
            class_type=data.class_type,
            academic_year_id=data.academic_year_id,
        )
        db.add(class_group)
        db.commit()
        db.refresh(class_group)

        resp = ClassGroupResponse.model_validate(class_group)
        if class_group.grade:
            resp.grade_name = class_group.grade.name
        return resp

    @staticmethod
    def update_class(db: Session, class_id: int, data: ClassGroupUpdate) -> ClassGroupResponse:
        """更新班级"""
        class_group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not class_group:
            raise ValueError("班级不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(class_group, key, value)

        db.commit()
        db.refresh(class_group)

        resp = ClassGroupResponse.model_validate(class_group)
        if class_group.grade:
            resp.grade_name = class_group.grade.name
        if class_group.head_teacher:
            resp.head_teacher_name = class_group.head_teacher.real_name
        return resp

    @staticmethod
    def delete_class(db: Session, class_id: int) -> bool:
        """删除班级"""
        class_group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not class_group:
            raise ValueError("班级不存在")

        db.delete(class_group)
        db.commit()
        return True

    @staticmethod
    def import_classes(db: Session, classes_data: List[ClassGroupCreate]) -> dict:
        """批量导入班级"""
        success_count = 0
        fail_count = 0
        errors = []

        for i, data in enumerate(classes_data):
            try:
                ClassService.create_class(db, data)
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(f"第{i + 1}条: {str(e)}")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors,
        }
