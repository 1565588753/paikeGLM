"""
科目相关的 Pydantic Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    """创建科目请求"""
    name: str = Field(..., max_length=50, description="科目名称")
    short_name: Optional[str] = Field(None, max_length=20, description="科目简称")
    subject_type: str = Field("副科", description="科目类型: 主科/副科/活动课")
    priority: int = Field(5, ge=1, le=10, description="优先级")
    allow_consecutive: bool = Field(False, description="是否允许连排")
    max_consecutive: int = Field(2, ge=1, description="最大连排节数")
    needs_special_room: bool = Field(False, description="是否需要专用教室")
    max_per_day: int = Field(2, ge=1, description="每天最大课时数")
    max_per_week: int = Field(10, ge=1, description="每周最大课时数")
    supports_odd_even: bool = Field(False, description="是否支持单双周")
    academic_year_id: int = Field(..., description="学年ID")


class SubjectUpdate(BaseModel):
    """更新科目请求"""
    name: Optional[str] = Field(None, max_length=50)
    short_name: Optional[str] = Field(None, max_length=20)
    subject_type: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    allow_consecutive: Optional[bool] = None
    max_consecutive: Optional[int] = Field(None, ge=1)
    needs_special_room: Optional[bool] = None
    max_per_day: Optional[int] = Field(None, ge=1)
    max_per_week: Optional[int] = Field(None, ge=1)
    supports_odd_even: Optional[bool] = None


class SubjectResponse(BaseModel):
    """科目响应"""
    id: int
    name: str
    short_name: Optional[str] = None
    subject_type: str
    priority: int
    allow_consecutive: bool
    max_consecutive: int
    needs_special_room: bool
    max_per_day: int
    max_per_week: int
    supports_odd_even: bool
    academic_year_id: int

    model_config = {"from_attributes": True}


class SubjectSubMappingCreate(BaseModel):
    """创建主科匹配小课请求"""
    subject_id: int = Field(..., description="主科ID")
    sub_subject_id: int = Field(..., description="小课ID")
    academic_year_id: int = Field(..., description="学年ID")
    enabled: bool = Field(True, description="是否启用")


class SubjectSubMappingResponse(BaseModel):
    """主科匹配小课响应"""
    id: int
    subject_id: int
    sub_subject_id: int
    academic_year_id: int
    enabled: bool
    # 关联信息
    subject_name: Optional[str] = None
    sub_subject_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SubjectListResponse(BaseModel):
    """科目列表响应"""
    items: List[SubjectResponse]
    total: int
    page: int
    page_size: int
