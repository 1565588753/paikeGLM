"""
备份记录和操作日志模型
- BackupRecord: 数据库备份记录
- OperationLog: 操作日志记录
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BackupRecord(Base):
    """备份记录模型"""
    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 备份文件名
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    # 文件路径
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件路径")
    # 文件大小 (字节)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="文件大小(字节)")
    # 备份类型: manual=手动, auto=自动
    backup_type: Mapped[str] = mapped_column(
        SAEnum("manual", "auto", name="backup_type_enum"),
        nullable=False, default="manual", comment="备份类型"
    )
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<BackupRecord(id={self.id}, filename={self.filename})>"


class OperationLog(Base):
    """操作日志模型 - 记录用户的关键操作"""
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 操作用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="用户ID"
    )
    # 操作动作 (如 create, update, delete, login, publish 等)
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作动作")
    # 操作目标类型 (如 user, class, subject, timetable 等)
    target_type: Mapped[str] = mapped_column(String(50), nullable=True, comment="目标类型")
    # 操作目标ID
    target_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="目标ID")
    # 操作详情
    detail: Mapped[str] = mapped_column(Text, nullable=True, comment="操作详情")
    # IP地址
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True, comment="IP地址")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # ==================== 关系定义 ====================
    user = relationship("User", back_populates="operation_logs")

    def __repr__(self):
        return f"<OperationLog(id={self.id}, action={self.action}, target_type={self.target_type})>"
