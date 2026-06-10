"""
作息时间模板和时间段相关的 Pydantic Schema
"""
from datetime import time
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 作息时间模板 Schema ====================

class ScheduleTemplateCreate(BaseModel):
    """创建作息时间模板请求"""
    name: str = Field(..., max_length=100, description="模板名称")
    grade_id: Optional[int] = Field(None, description="年级ID，null表示全校通用")
    academic_year_id: int = Field(..., description="学年ID")
    days_per_week: int = Field(5, ge=1, le=7, description="每周上课天数")
    is_default: bool = Field(False, description="是否默认模板")


class ScheduleTemplateResponse(BaseModel):
    """作息时间模板响应"""
    id: int
    name: str
    grade_id: Optional[int] = None
    academic_year_id: int
    days_per_week: int
    is_default: bool
    # 关联信息
    grade_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================== 时间段 Schema ====================

class TimeSlotCreate(BaseModel):
    """创建时间段请求"""
    schedule_template_id: int = Field(..., description="模板ID")
    day_of_week: int = Field(..., ge=1, le=7, description="星期几(1-7)")
    period_number: int = Field(..., ge=1, description="第几节")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    period_type: str = Field("上课", description="时段类型")
    label: Optional[str] = Field(None, max_length=20, description="标签")
    is_morning: bool = Field(False, description="是否上午")
    is_afternoon: bool = Field(False, description="是否下午")
    is_evening: bool = Field(False, description="是否晚自习")


class TimeSlotBatchUpdate(BaseModel):
    """批量更新时间段请求"""
    slots: List[TimeSlotCreate]


class TimeSlotResponse(BaseModel):
    """时间段响应"""
    id: int
    schedule_template_id: int
    day_of_week: int
    period_number: int
    start_time: time
    end_time: time
    period_type: str
    label: Optional[str] = None
    is_morning: bool
    is_afternoon: bool
    is_evening: bool

    model_config = {"from_attributes": True}
