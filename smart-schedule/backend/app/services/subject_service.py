"""
科目管理服务模块
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.subject import Subject, SubjectSubMapping
from app.schemas.subject import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SubjectSubMappingCreate, SubjectSubMappingResponse,
)


class SubjectService:
    """科目管理服务"""

    @staticmethod
    def list_subjects(
        db: Session,
        academic_year_id: Optional[int] = None,
        subject_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取科目列表"""
        query = db.query(Subject)

        if academic_year_id:
            query = query.filter(Subject.academic_year_id == academic_year_id)
        if subject_type:
            query = query.filter(Subject.subject_type == subject_type)

        total = query.count()
        subjects = query.order_by(Subject.priority.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = [SubjectResponse.model_validate(s) for s in subjects]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create_subject(db: Session, data: SubjectCreate) -> SubjectResponse:
        """创建科目"""
        # 检查名称是否重复
        existing = db.query(Subject).filter(
            Subject.name == data.name,
            Subject.academic_year_id == data.academic_year_id,
        ).first()
        if existing:
            raise ValueError(f"科目 {data.name} 已存在")

        subject = Subject(**data.model_dump())
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return SubjectResponse.model_validate(subject)

    @staticmethod
    def update_subject(db: Session, subject_id: int, data: SubjectUpdate) -> SubjectResponse:
        """更新科目"""
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise ValueError("科目不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(subject, key, value)

        db.commit()
        db.refresh(subject)
        return SubjectResponse.model_validate(subject)

    @staticmethod
    def delete_subject(db: Session, subject_id: int) -> bool:
        """删除科目"""
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise ValueError("科目不存在")

        db.delete(subject)
        db.commit()
        return True

    # ==================== 主科匹配小课 ====================

    @staticmethod
    def list_sub_mappings(db: Session, academic_year_id: Optional[int] = None) -> List[SubjectSubMappingResponse]:
        """获取主科匹配小课列表"""
        query = db.query(SubjectSubMapping)
        if academic_year_id:
            query = query.filter(SubjectSubMapping.academic_year_id == academic_year_id)

        mappings = query.all()
        items = []
        for m in mappings:
            resp = SubjectSubMappingResponse.model_validate(m)
            if m.main_subject:
                resp.subject_name = m.main_subject.name
            if m.sub_subject:
                resp.sub_subject_name = m.sub_subject.name
            items.append(resp)
        return items

    @staticmethod
    def create_sub_mapping(db: Session, data: SubjectSubMappingCreate) -> SubjectSubMappingResponse:
        """创建主科匹配小课"""
        mapping = SubjectSubMapping(**data.model_dump())
        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        resp = SubjectSubMappingResponse.model_validate(mapping)
        if mapping.main_subject:
            resp.subject_name = mapping.main_subject.name
        if mapping.sub_subject:
            resp.sub_subject_name = mapping.sub_subject.name
        return resp
