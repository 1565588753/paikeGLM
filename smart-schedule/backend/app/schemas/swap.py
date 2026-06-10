"""
调课请求相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CourseSwapCreate(BaseModel):
    """创建调课请求"""
    target_entry_id: int = Field(..., description="目标课表条目ID(想换到的位置)")
    requester_entry_id: int = Field(..., description="自己的课表条目ID(要换出的位置)")
    reason: Optional[str] = Field(None, description="调课原因")


class CourseSwapRespond(BaseModel):
    """响应调课请求"""
    approved: bool = Field(..., description="是否同意")
    reason: Optional[str] = Field(None, description="回复原因")


class CourseSwapResponse(BaseModel):
    """调课请求响应"""
    id: int
    requester_id: int
    target_id: int
    requester_entry_id: int
    target_entry_id: int
    reason: Optional[str] = None
    status: str
    responder_reason: Optional[str] = None
    academic_year_id: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    # 关联信息
    requester_name: Optional[str] = None
    target_name: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseSwapListResponse(BaseModel):
    """调课请求列表响应"""
    items: List[CourseSwapResponse]
    total: int
    page: int
    page_size: int
