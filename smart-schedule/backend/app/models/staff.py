"""
人事表模型
- StaffTableEntry: 人事表条目，记录年级-班级-科目-教师的对应关系
- 用于展示和管理全校任课情况的总览
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StaffTableEntry(Base):
    """人事表条目模型"""
    __tablename__ = "staff_table_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 年级
    grade_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False, comment="年级ID"
    )
    # 班级
    class_group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, comment="班级ID"
    )
    # 科目
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, comment="科目ID"
    )
    # 教师
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="教师ID"
    )
    # 每周课时数
    weekly_hours: Mapped[int] = mapped_column(Integer, nullable=False, comment="每周课时数")
    # 单双周类型
    odd_even_type: Mapped[str] = mapped_column(
        SAEnum("all", "odd", "even", name="staff_odd_even_enum"),
        nullable=False, default="all", comment="单双周类型"
    )
    # 备注
    notes: Mapped[str] = mapped_column(Text, nullable=True, comment="备注")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 所属学期
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, comment="学期ID"
    )

    # ==================== 关系定义 ====================
    grade = relationship("Grade", back_populates="staff_entries")
    class_group = relationship("ClassGroup", back_populates="staff_entries")
    subject = relationship("Subject", back_populates="staff_entries")
    teacher = relationship("User", back_populates="staff_entries")
    academic_year = relationship("AcademicYear", back_populates="staff_entries")
    semester = relationship("Semester", back_populates="staff_entries")

    def __repr__(self):
        return f"<StaffTableEntry(id={self.id}, grade={self.grade_id}, " \
               f"class={self.class_group_id}, subject={self.subject_id})>"
