"""
用户/教师模型
- 管理员和教师共用此模型
- 通过 role 字段区分角色
- 使用 bcrypt 加密密码
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """用户模型 - 包含管理员和教师"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 工号，唯一标识
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="工号")
    # bcrypt 加密后的密码
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    # 真实姓名
    real_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="真实姓名")
    # 性别
    gender: Mapped[str] = mapped_column(String(10), nullable=True, comment="性别")
    # 联系电话
    phone: Mapped[str] = mapped_column(String(20), nullable=True, comment="联系电话")
    # 角色: admin=管理员, teacher=教师
    role: Mapped[str] = mapped_column(
        SAEnum("admin", "teacher", name="user_role_enum"),
        nullable=False, default="teacher", comment="角色"
    )
    # 是否启用
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否启用")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间"
    )

    # ==================== 关系定义 ====================
    # 作为班主任的班级
    classes_as_head = relationship("ClassGroup", back_populates="head_teacher", foreign_keys="ClassGroup.head_teacher_id")
    # 任课安排
    teaching_assignments = relationship("TeachingAssignment", back_populates="teacher")
    # 课表条目
    timetable_entries = relationship("TimetableEntry", back_populates="teacher")
    # 调课请求 - 发起者
    swap_requests_initiated = relationship(
        "CourseSwapRequest", back_populates="requester",
        foreign_keys="CourseSwapRequest.requester_id"
    )
    # 调课请求 - 目标教师
    swap_requests_received = relationship(
        "CourseSwapRequest", back_populates="target",
        foreign_keys="CourseSwapRequest.target_id"
    )
    # 通知
    notifications = relationship("Notification", back_populates="user")
    # 操作日志
    operation_logs = relationship("OperationLog", back_populates="user")
    # 人事表条目
    staff_entries = relationship("StaffTableEntry", back_populates="teacher")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, real_name={self.real_name}, role={self.role})>"
