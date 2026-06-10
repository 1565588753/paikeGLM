"""
认证相关 API 路由
- POST /login - 登录
- POST /change-password - 修改密码
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_user, get_client_ip
from app.services.auth_service import AuthService
from app.schemas.user import LoginRequest, ChangePassword, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口

    - 使用工号和密码登录
    - 返回 JWT Token 和用户信息
    """
    ip_address = get_client_ip(request)
    return AuthService.login(db, data.username, data.password, ip_address)


@router.post("/change-password", summary="修改密码")
def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    修改密码接口

    - 需要验证旧密码
    - 新密码最少6位
    """
    AuthService.change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "密码修改成功"}
