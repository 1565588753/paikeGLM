"""
科目模型
- Subject: 科目 (如语文、数学)
- SubjectSubMapping: 语数外匹配小课 (如语文匹配综合实践)
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subject(Base):
    """科目模型"""
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 科目名称
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="科目名称")
    # 科目简称
    short_name: Mapped[str] = mapped_column(String(20), nullable=True, comment="科目简称")
    # 科目类型: 主科/副科/活动课
    subject_type: Mapped[str] = mapped_column(
        SAEnum("主科", "副科", "活动课", name="subject_type_enum"),
        nullable=False, default="副科", comment="科目类型"
    )
    # 优先级（数值越大优先级越高，排课时优先安排）
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="优先级")
    # 是否允许连排
    allow_consecutive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否允许连排")
    # 最大连排节数
    max_consecutive: Mapped[int] = mapped_column(Integer, default=2, nullable=False, comment="最大连排节数")
    # 是否需要专用教室
    needs_special_room: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否需要专用教室")
    # 每天最大课时数
    max_per_day: Mapped[int] = mapped_column(Integer, default=2, nullable=False, comment="每天最大课时数")
    # 每周最大课时数
    max_per_week: Mapped[int] = mapped_column(Integer, default=10, nullable=False, comment="每周最大课时数")
    # 是否支持单双周
    supports_odd_even: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否支持单双周")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )

    # ==================== 关系定义 ====================
    academic_year = relationship("AcademicYear", back_populates="subjects")
    teaching_assignments = relationship("TeachingAssignment", back_populates="subject")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")
    staff_entries = relationship("StaffTableEntry", back_populates="subject")
    # 作为主科的小课映射
    sub_mappings = relationship("SubjectSubMapping", back_populates="main_subject", foreign_keys="SubjectSubMapping.subject_id")
    # 作为小课的主科映射
    main_mappings = relationship("SubjectSubMapping", back_populates="sub_subject", foreign_keys="SubjectSubMapping.sub_subject_id")

    def __repr__(self):
        return f"<Subject(id={self.id}, name={self.name}, subject_type={self.subject_type})>"


class SubjectSubMapping(Base):
    """语数外匹配小课模型 - 主科可关联小课，排课时优先安排在主科后面"""
    __tablename__ = "subject_sub_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 主科ID (如语文)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, comment="主科ID"
    )
    # 小课ID (如综合实践)
    sub_subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, comment="小课ID"
    )
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否启用")

    # ==================== 关系定义 ====================
    main_subject = relationship("Subject", back_populates="sub_mappings", foreign_keys=[subject_id])
    sub_subject = relationship("Subject", back_populates="main_mappings", foreign_keys=[sub_subject_id])

    def __repr__(self):
        return f"<SubjectSubMapping(id={self.id}, subject_id={self.subject_id}, sub_subject_id={self.sub_subject_id})>"
