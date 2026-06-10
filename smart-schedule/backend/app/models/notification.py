"""
通知模型
- 支持多种通知类型
- 与用户一对多关联
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 接收用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    # 通知类型
    type: Mapped[str] = mapped_column(
        SAEnum(
            "swap_request", "swap_result", "schedule_published",
            "year_switch", "staff_update", name="notification_type_enum"
        ),
        nullable=False, comment="通知类型"
    )
    # 通知标题
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    # 通知内容
    content: Mapped[str] = mapped_column(Text, nullable=True, comment="内容")
    # 是否已读
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否已读")
    # 关联ID (如调课请求ID、方案ID等)
    related_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="关联ID")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # ==================== 关系定义 ====================
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, title={self.title})>"
