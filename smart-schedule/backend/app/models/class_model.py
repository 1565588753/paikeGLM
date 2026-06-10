"""
班级模型
- ClassGroup: 班级/班级组
- 支持普通班、实验班、特长班等类型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ClassGroup(Base):
    """班级模型"""
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 班级全名，如 "高一(1)班"
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="班级名称")
    # 班级简称，如 "1班"
    short_name: Mapped[str] = mapped_column(String(20), nullable=True, comment="班级简称")
    # 所属年级
    grade_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False, comment="年级ID"
    )
    # 学生人数
    student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="学生人数")
    # 班主任
    head_teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="班主任ID"
    )
    # 班级类型: 普通班/实验班/特长班
    class_type: Mapped[str] = mapped_column(
        SAEnum("普通班", "实验班", "特长班", name="class_type_enum"),
        nullable=False, default="普通班", comment="班级类型"
    )
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )

    # ==================== 关系定义 ====================
    grade = relationship("Grade", back_populates="classes")
    head_teacher = relationship("User", back_populates="classes_as_head", foreign_keys=[head_teacher_id])
    academic_year = relationship("AcademicYear", back_populates="classes")
    teaching_assignments = relationship("TeachingAssignment", back_populates="class_group")
    timetable_entries = relationship("TimetableEntry", back_populates="class_group")
    staff_entries = relationship("StaffTableEntry", back_populates="class_group")

    def __repr__(self):
        return f"<ClassGroup(id={self.id}, name={self.name}, class_type={self.class_type})>"
