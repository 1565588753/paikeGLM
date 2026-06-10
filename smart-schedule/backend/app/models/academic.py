"""
学年/学期/年级模型
- AcademicYear: 学年 (如 "2024-2025")
- Semester: 学期 (上学期/下学期)
- Grade: 年级 (如 "高一")
"""
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Boolean, Integer, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AcademicYear(Base):
    """学年模型"""
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 学年名称，如 "2024-2025"
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="学年名称")
    # 状态: active=当前, archived=已归档, pending=待启用
    status: Mapped[str] = mapped_column(
        SAEnum("active", "archived", "pending", name="academic_year_status_enum"),
        nullable=False, default="pending", comment="状态"
    )
    # 是否为当前学年
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否当前学年")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # ==================== 关系定义 ====================
    semesters = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="academic_year", cascade="all, delete-orphan")
    classes = relationship("ClassGroup", back_populates="academic_year")
    subjects = relationship("Subject", back_populates="academic_year")
    classrooms = relationship("Classroom", back_populates="academic_year")
    schedule_templates = relationship("ScheduleTemplate", back_populates="academic_year")
    teaching_assignments = relationship("TeachingAssignment", back_populates="academic_year")
    schedule_plans = relationship("SchedulePlan", back_populates="academic_year")
    staff_entries = relationship("StaffTableEntry", back_populates="academic_year")

    def __repr__(self):
        return f"<AcademicYear(id={self.id}, name={self.name}, is_current={self.is_current})>"


class Semester(Base):
    """学期模型 - 每学年两个学期"""
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 学期名称: 上学期/下学期
    name: Mapped[str] = mapped_column(
        SAEnum("上学期", "下学期", name="semester_name_enum"),
        nullable=False, comment="学期名称"
    )
    # 开学日期
    start_date: Mapped[date] = mapped_column(Date, nullable=True, comment="开学日期")
    # 结束日期
    end_date: Mapped[date] = mapped_column(Date, nullable=True, comment="结束日期")
    # 是否为当前学期
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否当前学期")
    # 状态
    status: Mapped[str] = mapped_column(
        SAEnum("active", "archived", "pending", name="semester_status_enum"),
        nullable=False, default="pending", comment="状态"
    )

    # ==================== 关系定义 ====================
    academic_year = relationship("AcademicYear", back_populates="semesters")
    teaching_assignments = relationship("TeachingAssignment", back_populates="semester")
    schedule_plans = relationship("SchedulePlan", back_populates="semester")
    staff_entries = relationship("StaffTableEntry", back_populates="semester")

    def __repr__(self):
        return f"<Semester(id={self.id}, name={self.name}, academic_year_id={self.academic_year_id})>"


class Grade(Base):
    """年级模型"""
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 年级名称，如 "高一"、"高二"、"高三"
    name: Mapped[str] = mapped_column(String(20), nullable=False, comment="年级名称")
    # 年级层级，用于排序 (1-12)
    level: Mapped[int] = mapped_column(Integer, nullable=False, comment="年级层级")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )

    # ==================== 关系定义 ====================
    academic_year = relationship("AcademicYear", back_populates="grades")
    classes = relationship("ClassGroup", back_populates="grade", cascade="all, delete-orphan")
    schedule_templates = relationship("ScheduleTemplate", back_populates="grade")
    staff_entries = relationship("StaffTableEntry", back_populates="grade")

    def __repr__(self):
        return f"<Grade(id={self.id}, name={self.name}, level={self.level})>"
