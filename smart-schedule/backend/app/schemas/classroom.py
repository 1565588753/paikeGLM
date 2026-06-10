"""
教室相关的 Pydantic Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    """创建教室请求"""
    name: str = Field(..., max_length=50, description="教室名称")
    room_type: str = Field("普通教室", description="教室类型")
    capacity: int = Field(50, ge=1, description="容纳人数")
    location: Optional[str] = Field(None, max_length=100, description="位置")
    equipment: Optional[str] = Field(None, description="设备描述")
    academic_year_id: int = Field(..., description="学年ID")


class ClassroomUpdate(BaseModel):
    """更新教室请求"""
    name: Optional[str] = Field(None, max_length=50)
    room_type: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = Field(None, max_length=100)
    equipment: Optional[str] = None


class ClassroomResponse(BaseModel):
    """教室响应"""
    id: int
    name: str
    room_type: str
    capacity: int
    location: Optional[str] = None
    equipment: Optional[str] = None
    academic_year_id: int

    model_config = {"from_attributes": True}


class ClassroomListResponse(BaseModel):
    """教室列表响应"""
    items: List[ClassroomResponse]
    total: int
    page: int
    page_size: int
