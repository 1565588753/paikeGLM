"""
认证服务模块
- 用户登录验证
- JWT Token 生成
- 密码修改
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.backup import OperationLog
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.schemas.user import TokenResponse, UserResponse


class AuthService:
    """认证服务"""

    @staticmethod
    def login(db: Session, username: str, password: str, ip_address: str = "") -> TokenResponse:
        """
        用户登录

        流程：
        1. 根据工号查找用户
        2. 验证密码
        3. 检查用户状态
        4. 生成 JWT Token
        5. 记录登录日志
        """
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("用户名或密码错误")

        # 验证密码
        if not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise ValueError("用户已被禁用，请联系管理员")

        # 生成 JWT Token
        token = create_access_token(data={"sub": user.id, "role": user.role})

        # 记录登录日志
        log = OperationLog(
            user_id=user.id,
            action="login",
            target_type="user",
            target_id=user.id,
            detail=f"用户 {user.real_name} 登录系统",
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def change_password(
        db: Session, user: User, old_password: str, new_password: str
    ) -> bool:
        """
        修改密码

        流程：
        1. 验证旧密码
        2. 生成新密码哈希
        3. 更新数据库
        """
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.now()
        db.commit()

        return True
