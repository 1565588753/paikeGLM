"""
课表相关模型 (核心)
- TeachingAssignment: 任课安排 (哪个老师教哪个班的哪门课)
- PreScheduledCourse: 预排课程 (手动固定的课程)
- SchedulePlan: 排课方案
- TimetableEntry: 课表条目 (最终生成的课表)
"""
from datetime import time, datetime
from sqlalchemy import (
    String, Integer, Boolean, Time, DateTime, Enum as SAEnum,
    ForeignKey, JSON, Text, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TeachingAssignment(Base):
    """任课安排模型 - 记录哪个老师教哪个班的哪门课"""
    __tablename__ = "teaching_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    # 单双周类型: all=每周, odd=单周, even=双周
    odd_even_type: Mapped[str] = mapped_column(
        SAEnum("all", "odd", "even", name="odd_even_enum"),
        nullable=False, default="all", comment="单双周类型"
    )
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 所属学期
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, comment="学期ID"
    )
    # 是否合班课
    is_combined_class: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否合班课")
    # 合班班级ID列表 (JSON格式)
    combined_class_ids: Mapped[str] = mapped_column(JSON, nullable=True, comment="合班班级ID列表")
    # 备注
    notes: Mapped[str] = mapped_column(Text, nullable=True, comment="备注")

    # ==================== 关系定义 ====================
    class_group = relationship("ClassGroup", back_populates="teaching_assignments")
    subject = relationship("Subject", back_populates="teaching_assignments")
    teacher = relationship("User", back_populates="teaching_assignments")
    academic_year = relationship("AcademicYear", back_populates="teaching_assignments")
    semester = relationship("Semester", back_populates="teaching_assignments")
    pre_scheduled_courses = relationship("PreScheduledCourse", back_populates="teaching_assignment")
    timetable_entries = relationship("TimetableEntry", back_populates="teaching_assignment")

    def __repr__(self):
        return f"<TeachingAssignment(id={self.id}, class={self.class_group_id}, " \
               f"subject={self.subject_id}, teacher={self.teacher_id})>"


class PreScheduledCourse(Base):
    """预排课程模型 - 手动固定某课在某时间段"""
    __tablename__ = "pre_scheduled_courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 任课安排
    teaching_assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teaching_assignments.id", ondelete="CASCADE"), nullable=False,
        comment="任课安排ID"
    )
    # 星期几
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="星期几(1-7)")
    # 第几节
    period_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="第几节")
    # 作息时间模板
    schedule_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False,
        comment="作息时间模板ID"
    )
    # 单双周类型
    odd_even_type: Mapped[str] = mapped_column(
        SAEnum("all", "odd", "even", name="pre_scheduled_odd_even_enum"),
        nullable=False, default="all", comment="单双周类型"
    )
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )

    # ==================== 关系定义 ====================
    teaching_assignment = relationship("TeachingAssignment", back_populates="pre_scheduled_courses")
    schedule_template = relationship("ScheduleTemplate", back_populates="pre_scheduled_courses")

    def __repr__(self):
        return f"<PreScheduledCourse(id={self.id}, day={self.day_of_week}, period={self.period_number})>"


class SchedulePlan(Base):
    """排课方案模型 - 每次排课生成一个方案"""
    __tablename__ = "schedule_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 方案名称
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="方案名称")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 所属学期
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, comment="学期ID"
    )
    # 状态: draft=草稿, published=已发布
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "published", name="plan_status_enum"),
        nullable=False, default="draft", comment="状态"
    )
    # 是否为当前激活方案
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否激活")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间"
    )

    # ==================== 关系定义 ====================
    academic_year = relationship("AcademicYear", back_populates="schedule_plans")
    semester = relationship("Semester", back_populates="schedule_plans")
    timetable_entries = relationship("TimetableEntry", back_populates="schedule_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SchedulePlan(id={self.id}, name={self.name}, status={self.status})>"


class TimetableEntry(Base):
    """
    课表条目模型 (核心)
    - 存储最终生成的课表数据
    - start_time/end_time 冗余存储用于快速冲突检测，无需 JOIN time_slots 表
    """
    __tablename__ = "timetable_entries"
    __table_args__ = (
        # 复合索引：按方案+班级+星期+节次查询
        Index("idx_plan_class_day_period", "schedule_plan_id", "class_group_id", "day_of_week", "period_number"),
        # 复合索引：按方案+教师+星期查询（教师课表视图）
        Index("idx_plan_teacher_day", "schedule_plan_id", "teacher_id", "day_of_week"),
        # 复合索引：按方案+教室+星期查询（教室使用视图）
        Index("idx_plan_classroom_day", "schedule_plan_id", "classroom_id", "day_of_week"),
        # 复合索引：冲突检测用 - 教师同天同时间段
        Index("idx_teacher_day_time", "teacher_id", "day_of_week", "start_time", "end_time"),
        # 复合索引：冲突检测用 - 班级同天同时间段
        Index("idx_class_day_time", "class_group_id", "day_of_week", "start_time", "end_time"),
        # 复合索引：冲突检测用 - 教室同天同时间段
        Index("idx_classroom_day_time", "classroom_id", "day_of_week", "start_time", "end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 所属排课方案
    schedule_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule_plans.id", ondelete="CASCADE"), nullable=False, comment="排课方案ID"
    )
    # 任课安排
    teaching_assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teaching_assignments.id", ondelete="CASCADE"), nullable=False, comment="任课安排ID"
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
    # 教室 (nullable 表示未分配教室)
    classroom_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True, comment="教室ID"
    )
    # 星期几
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="星期几(1-7)")
    # 第几节
    period_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="第几节")
    # 作息时间模板
    schedule_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False,
        comment="作息时间模板ID"
    )
    # 开始时间 (冗余存储，用于快速冲突检测)
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment="开始时间")
    # 结束时间 (冗余存储，用于快速冲突检测)
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment="结束时间")
    # 单双周类型
    odd_even_type: Mapped[str] = mapped_column(
        SAEnum("all", "odd", "even", name="entry_odd_even_enum"),
        nullable=False, default="all", comment="单双周类型"
    )
    # 是否锁定 (锁定的条目不会被自动排课修改)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否锁定")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间"
    )

    # ==================== 关系定义 ====================
    schedule_plan = relationship("SchedulePlan", back_populates="timetable_entries")
    teaching_assignment = relationship("TeachingAssignment", back_populates="timetable_entries")
    class_group = relationship("ClassGroup", back_populates="timetable_entries")
    subject = relationship("Subject", back_populates="timetable_entries")
    teacher = relationship("User", back_populates="timetable_entries")
    classroom = relationship("Classroom", back_populates="timetable_entries")
    schedule_template = relationship("ScheduleTemplate", back_populates="timetable_entries")

    def __repr__(self):
        return f"<TimetableEntry(id={self.id}, day={self.day_of_week}, period={self.period_number}, " \
               f"class={self.class_group_id}, teacher={self.teacher_id})>"
