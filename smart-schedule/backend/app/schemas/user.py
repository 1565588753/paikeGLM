"""
用户相关的 Pydantic Schema
- 用于请求参数验证和响应数据序列化
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 请求 Schema ====================

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=2, max_length=50, description="工号")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    real_name: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    gender: Optional[str] = Field(None, description="性别")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    role: str = Field("teacher", description="角色: admin/teacher")


class UserUpdate(BaseModel):
    """更新用户请求"""
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")
    gender: Optional[str] = Field(None, description="性别")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    role: Optional[str] = Field(None, description="角色")
    is_active: Optional[bool] = Field(None, description="是否启用")


class UserImport(BaseModel):
    """批量导入用户"""
    users: List[UserCreate]


class ChangePassword(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="工号")
    password: str = Field(..., description="密码")


# ==================== 响应 Schema ====================

class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    real_name: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
