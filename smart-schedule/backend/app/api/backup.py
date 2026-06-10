"""
备份管理 API 路由
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.backup import OperationLog
from app.utils.deps import get_current_admin, get_client_ip
from app.services.backup_service import BackupService

router = APIRouter()


@router.get("", summary="获取备份列表")
def list_backups(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取备份列表（仅管理员）"""
    return BackupService.list_backups(db, page, page_size)


@router.post("", summary="创建手动备份")
def create_backup(
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    创建手动备份（仅管理员）

    - 使用 mysqldump 进行数据库备份
    """
    result = BackupService.create_backup(db, "manual")

    log = OperationLog(
        user_id=current_user.id,
        action="backup",
        target_type="backup",
        detail=f"创建手动备份: {result.filename}",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return result


@router.post("/{backup_id}/restore", summary="从备份恢复")
def restore_backup(
    backup_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    从备份恢复数据库（仅管理员）

    警告：此操作会覆盖当前数据库数据
    """
    BackupService.restore_backup(db, backup_id)

    log = OperationLog(
        user_id=current_user.id,
        action="restore",
        target_type="backup",
        target_id=backup_id,
        detail="从备份恢复数据库",
        ip_address=get_client_ip(request) if request else "",
    )
    db.add(log)
    db.commit()

    return {"message": "恢复成功"}
