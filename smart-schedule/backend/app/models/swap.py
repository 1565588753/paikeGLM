"""
调课请求模型
- CourseSwapRequest: 教师之间的调课请求
- 支持完整的调课审批流程
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CourseSwapRequest(Base):
    """调课请求模型"""
    __tablename__ = "course_swap_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 请求发起者
    requester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="请求者ID"
    )
    # 目标教师 (被请求调课的教师)
    target_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="目标教师ID"
    )
    # 请求者要换出的课表条目
    requester_entry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("timetable_entries.id", ondelete="CASCADE"), nullable=False,
        comment="请求者课表条目ID"
    )
    # 目标教师要换出的课表条目
    target_entry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("timetable_entries.id", ondelete="CASCADE"), nullable=False,
        comment="目标课表条目ID"
    )
    # 调课原因
    reason: Mapped[str] = mapped_column(Text, nullable=True, comment="调课原因")
    # 状态: pending=待审批, approved=已同意, rejected=已拒绝, cancelled=已取消
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "approved", "rejected", "cancelled", name="swap_status_enum"),
        nullable=False, default="pending", comment="状态"
    )
    # 审批回复原因
    responder_reason: Mapped[str] = mapped_column(Text, nullable=True, comment="审批回复原因")
    # 所属学年
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, comment="学年ID"
    )
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间"
    )
    # 处理时间
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="处理时间")

    # ==================== 关系定义 ====================
    requester = relationship("User", back_populates="swap_requests_initiated", foreign_keys=[requester_id])
    target = relationship("User", back_populates="swap_requests_received", foreign_keys=[target_id])
    requester_entry = relationship("TimetableEntry", foreign_keys=[requester_entry_id])
    target_entry = relationship("TimetableEntry", foreign_keys=[target_entry_id])

    def __repr__(self):
        return f"<CourseSwapRequest(id={self.id}, requester={self.requester_id}, " \
               f"target={self.target_id}, status={self.status})>"
