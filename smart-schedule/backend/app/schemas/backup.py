"""
备份和操作日志相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 备份 Schema ====================

class BackupResponse(BaseModel):
    """备份记录响应"""
    id: int
    filename: str
    file_path: str
    file_size: int
    backup_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BackupListResponse(BaseModel):
    """备份列表响应"""
    items: List[BackupResponse]
    total: int


# ==================== 操作日志 Schema ====================

class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: int
    user_id: Optional[int] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    # 关联信息
    username: Optional[str] = None
    real_name: Optional[str] = None

    model_config = {"from_attributes": True}


class OperationLogListResponse(BaseModel):
    """操作日志列表响应"""
    items: List[OperationLogResponse]
    total: int
    page: int
    page_size: int
