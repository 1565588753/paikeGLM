"""
教室模型
- 支持多种教室类型：普通教室、多媒体教室、实验室等
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Classroom(Base):
    """教室模型"""
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 教室名称，如 "101教室"
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="教室名称")
    # 教室类型: 普通教室/多媒体教室/实验室/音乐室/美术室/体育馆
    room_type: Mapped[str] = mapped_column(
        SAEnum("普通教室", "多媒体教室", "实验室", "音乐室", "美术室", "体育馆", name="room_type_enum"),
        nullable=False, default="普通教室", comment="教室类型"
    )
    # 容纳人数
    capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False, comment="容纳人数")
    # 位置描述
    location: Mapped[str] = mapped_column(String(100), nullable=True, comment="位置")
    # 设备描述
    equipment: Mapped[str] = mapped_column(Text, nullable=True, comment="设备描述")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )

    # ==================== 关系定义 ====================
    academic_year = relationship("AcademicYear", back_populates="classrooms")
    timetable_entries = relationship("TimetableEntry", back_populates="classroom")

    def __repr__(self):
        return f"<Classroom(id={self.id}, name={self.name}, room_type={self.room_type})>"
