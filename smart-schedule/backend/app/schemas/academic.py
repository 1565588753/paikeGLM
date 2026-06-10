"""
学年/学期/年级相关的 Pydantic Schema
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 学年 Schema ====================

class AcademicYearCreate(BaseModel):
    """创建学年请求"""
    name: str = Field(..., max_length=20, description="学年名称，如 2024-2025")


class AcademicYearResponse(BaseModel):
    """学年响应"""
    id: int
    name: str
    status: str
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 学期 Schema ====================

class SemesterCreate(BaseModel):
    """创建学期请求"""
    academic_year_id: int = Field(..., description="学年ID")
    name: str = Field(..., description="学期名称: 上学期/下学期")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SemesterResponse(BaseModel):
    """学期响应"""
    id: int
    academic_year_id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    status: str

    model_config = {"from_attributes": True}


# ==================== 年级 Schema ====================

class GradeCreate(BaseModel):
    """创建年级请求"""
    name: str = Field(..., max_length=20, description="年级名称")
    level: int = Field(..., ge=1, le=12, description="年级层级(1-12)")
    academic_year_id: int = Field(..., description="学年ID")


class GradeResponse(BaseModel):
    """年级响应"""
    id: int
    name: str
    level: int
    academic_year_id: int

    model_config = {"from_attributes": True}


# ==================== 学年切换 ====================

class YearSwitchResponse(BaseModel):
    """学年切换响应"""
    message: str
    old_year_id: int
    new_year_id: int
