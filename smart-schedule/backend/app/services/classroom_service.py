"""
教室管理服务模块
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse


class ClassroomService:
    """教室管理服务"""

    @staticmethod
    def list_classrooms(
        db: Session,
        academic_year_id: Optional[int] = None,
        room_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取教室列表"""
        query = db.query(Classroom)

        if academic_year_id:
            query = query.filter(Classroom.academic_year_id == academic_year_id)
        if room_type:
            query = query.filter(Classroom.room_type == room_type)

        total = query.count()
        classrooms = query.offset((page - 1) * page_size).limit(page_size).all()

        items = [ClassroomResponse.model_validate(c) for c in classrooms]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create_classroom(db: Session, data: ClassroomCreate) -> ClassroomResponse:
        """创建教室"""
        existing = db.query(Classroom).filter(
            Classroom.name == data.name,
            Classroom.academic_year_id == data.academic_year_id,
        ).first()
        if existing:
            raise ValueError(f"教室 {data.name} 已存在")

        classroom = Classroom(**data.model_dump())
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return ClassroomResponse.model_validate(classroom)

    @staticmethod
    def update_classroom(db: Session, classroom_id: int, data: ClassroomUpdate) -> ClassroomResponse:
        """更新教室"""
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise ValueError("教室不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(classroom, key, value)

        db.commit()
        db.refresh(classroom)
        return ClassroomResponse.model_validate(classroom)

    @staticmethod
    def delete_classroom(db: Session, classroom_id: int) -> bool:
        """删除教室"""
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise ValueError("教室不存在")

        db.delete(classroom)
        db.commit()
        return True
