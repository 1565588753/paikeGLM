"""
用户管理 API 路由
- GET / - 用户列表
- POST / - 创建用户
- PUT /{id} - 更新用户
- DELETE /{id} - 删除用户
- POST /import - 批量导入
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_user, get_current_admin, get_client_ip
from app.utils.security import get_password_hash
from app.schemas.user import UserCreate, UserUpdate, UserImport, UserResponse, UserListResponse

router = APIRouter()


@router.get("", response_model=UserListResponse, summary="获取用户列表")
def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（仅管理员）

    - 支持按角色和状态筛选
    - 支持分页
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [UserResponse.model_validate(u) for u in users]
    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=UserResponse, summary="创建用户")
def create_user(
    data: UserCreate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    创建用户（仅管理员）

    - 工号唯一
    - 密码使用 bcrypt 加密
    """
    # 检查工号是否重复
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"工号 {data.username} 已存在")

    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name,
        gender=data.gender,
        phone=data.phone,
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        target_type="user",
        target_id=user.id,
        detail=f"创建用户 {user.real_name}({user.username})",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新用户信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        target_type="user",
        target_id=user.id,
        detail=f"更新用户 {user.real_name}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除用户（仅管理员）"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        target_type="user",
        target_id=user.id,
        detail=f"删除用户 {user.real_name}({user.username})",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)

    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.post("/import", summary="批量导入用户")
def import_users(
    data: UserImport,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """批量导入用户（仅管理员）"""
    success_count = 0
    fail_count = 0
    errors = []

    for i, user_data in enumerate(data.users):
        try:
            existing = db.query(User).filter(User.username == user_data.username).first()
            if existing:
                raise ValueError(f"工号 {user_data.username} 已存在")

            user = User(
                username=user_data.username,
                password_hash=get_password_hash(user_data.password),
                real_name=user_data.real_name,
                gender=user_data.gender,
                phone=user_data.phone,
                role=user_data.role,
                is_active=True,
            )
            db.add(user)
            success_count += 1
        except Exception as e:
            fail_count += 1
            errors.append(f"第{i + 1}条: {str(e)}")

    db.commit()

    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        action="import",
        target_type="user",
        detail=f"批量导入用户: 成功{success_count}个，失败{fail_count}个",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors,
    }
