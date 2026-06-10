"""
作息时间模板和时间段模型
- ScheduleTemplate: 作息时间模板 (可按年级定制)
- TimeSlot: 具体的时间段定义
"""
from datetime import time, datetime
from sqlalchemy import String, Integer, Boolean, Time, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ScheduleTemplate(Base):
    """作息时间模板 - 定义一周几天的作息安排"""
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 模板名称
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    # 关联年级 (nullable 表示全校通用默认模板)
    grade_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grades.id", ondelete="SET NULL"), nullable=True, comment="年级ID"
    )
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 每周上课天数
    days_per_week: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="每周上课天数")
    # 是否为默认模板
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否默认模板")

    # ==================== 关系定义 ====================
    grade = relationship("Grade", back_populates="schedule_templates")
    academic_year = relationship("AcademicYear", back_populates="schedule_templates")
    time_slots = relationship("TimeSlot", back_populates="schedule_template", cascade="all, delete-orphan",
                              order_by="TimeSlot.day_of_week, TimeSlot.period_number")
    pre_scheduled_courses = relationship("PreScheduledCourse", back_populates="schedule_template")
    timetable_entries = relationship("TimetableEntry", back_populates="schedule_template")

    def __repr__(self):
        return f"<ScheduleTemplate(id={self.id}, name={self.name})>"


class TimeSlot(Base):
    """时间段模型 - 定义每个时间段的起止时间和类型"""
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 所属模板
    schedule_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False, comment="模板ID"
    )
    # 星期几 (1=周一, 7=周日)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="星期几(1-7)")
    # 第几节课
    period_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="第几节")
    # 开始时间
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment="开始时间")
    # 结束时间
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment="结束时间")
    # 时段类型: 上课/课间操/眼保健操/午休/晚自习
    period_type: Mapped[str] = mapped_column(
        SAEnum("上课", "课间操", "眼保健操", "午休", "晚自习", name="period_type_enum"),
        nullable=False, default="上课", comment="时段类型"
    )
    # 标签，如 "第一节"
    label: Mapped[str] = mapped_column(String(20), nullable=True, comment="标签")
    # 是否上午
    is_morning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否上午")
    # 是否下午
    is_afternoon: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否下午")
    # 是否晚自习
    is_evening: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否晚自习")

    # ==================== 关系定义 ====================
    schedule_template = relationship("ScheduleTemplate", back_populates="time_slots")

    def __repr__(self):
        return f"<TimeSlot(id={self.id}, day={self.day_of_week}, period={self.period_number}, " \
               f"{self.start_time}-{self.end_time})>"
