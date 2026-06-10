"""
人事表相关的 Pydantic Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class StaffEntryUpdate(BaseModel):
    """更新人事表条目请求"""
    teacher_id: Optional[int] = Field(None, description="教师ID")
    weekly_hours: Optional[int] = Field(None, ge=1, description="每周课时数")
    odd_even_type: Optional[str] = Field(None, description="单双周类型")
    notes: Optional[str] = Field(None, description="备注")


class StaffEntryImport(BaseModel):
    """批量导入人事表"""
    entries: List[dict]


class StaffEntryResponse(BaseModel):
    """人事表条目响应"""
    id: int
    grade_id: int
    class_group_id: int
    subject_id: int
    teacher_id: int
    weekly_hours: int
    odd_even_type: str
    notes: Optional[str] = None
    academic_year_id: int
    semester_id: int
    # 关联信息
    grade_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None

    model_config = {"from_attributes": True}


class StaffEntryListResponse(BaseModel):
    """人事表列表响应"""
    items: List[StaffEntryResponse]
    total: int
    page: int
    page_size: int
