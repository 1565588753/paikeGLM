"""
课表相关的 Pydantic Schema
- 任课安排、预排课程、排课方案、课表条目
"""
from datetime import time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 任课安排 Schema ====================

class TeachingAssignmentCreate(BaseModel):
    """创建任课安排请求"""
    class_group_id: int = Field(..., description="班级ID")
    subject_id: int = Field(..., description="科目ID")
    teacher_id: int = Field(..., description="教师ID")
    weekly_hours: int = Field(..., ge=1, description="每周课时数")
    odd_even_type: str = Field("all", description="单双周类型: all/odd/even")
    academic_year_id: int = Field(..., description="学年ID")
    semester_id: int = Field(..., description="学期ID")
    is_combined_class: bool = Field(False, description="是否合班课")
    combined_class_ids: Optional[List[int]] = Field(None, description="合班班级ID列表")
    notes: Optional[str] = Field(None, description="备注")


class TeachingAssignmentImport(BaseModel):
    """批量导入任课安排"""
    assignments: List[TeachingAssignmentCreate]


class TeachingAssignmentResponse(BaseModel):
    """任课安排响应"""
    id: int
    class_group_id: int
    subject_id: int
    teacher_id: int
    weekly_hours: int
    odd_even_type: str
    academic_year_id: int
    semester_id: int
    is_combined_class: bool
    combined_class_ids: Optional[List[int]] = None
    notes: Optional[str] = None
    # 关联信息
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================== 预排课程 Schema ====================

class PreScheduledCourseCreate(BaseModel):
    """创建预排课程请求"""
    teaching_assignment_id: int = Field(..., description="任课安排ID")
    day_of_week: int = Field(..., ge=1, le=7, description="星期几")
    period_number: int = Field(..., ge=1, description="第几节")
    schedule_template_id: int = Field(..., description="作息时间模板ID")
    odd_even_type: str = Field("all", description="单双周类型")
    academic_year_id: int = Field(..., description="学年ID")


class PreScheduledCourseResponse(BaseModel):
    """预排课程响应"""
    id: int
    teaching_assignment_id: int
    day_of_week: int
    period_number: int
    schedule_template_id: int
    odd_even_type: str
    academic_year_id: int

    model_config = {"from_attributes": True}


# ==================== 排课方案 Schema ====================

class SchedulePlanCreate(BaseModel):
    """创建排课方案请求"""
    name: str = Field(..., max_length=100, description="方案名称")
    academic_year_id: int = Field(..., description="学年ID")
    semester_id: int = Field(..., description="学期ID")


class SchedulePlanResponse(BaseModel):
    """排课方案响应"""
    id: int
    name: str
    academic_year_id: int
    semester_id: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==================== 课表条目 Schema ====================

class TimetableEntryResponse(BaseModel):
    """课表条目响应"""
    id: int
    schedule_plan_id: int
    teaching_assignment_id: int
    class_group_id: int
    subject_id: int
    teacher_id: int
    classroom_id: Optional[int] = None
    day_of_week: int
    period_number: int
    schedule_template_id: int
    start_time: time
    end_time: time
    odd_even_type: str
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    # 关联信息
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    subject_short_name: Optional[str] = None
    teacher_name: Optional[str] = None
    classroom_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TimetableMoveRequest(BaseModel):
    """移动课表条目请求 (拖拽操作)"""
    day_of_week: int = Field(..., ge=1, le=7, description="目标星期几")
    period_number: int = Field(..., ge=1, description="目标第几节")
    classroom_id: Optional[int] = Field(None, description="目标教室ID")


class ConflictCheckRequest(BaseModel):
    """冲突检查请求"""
    entry_id: int = Field(..., description="课表条目ID")
    day_of_week: int = Field(..., ge=1, le=7, description="目标星期几")
    period_number: int = Field(..., ge=1, description="目标第几节")
    classroom_id: Optional[int] = Field(None, description="目标教室ID")


class ConflictCheckResponse(BaseModel):
    """冲突检查响应"""
    has_conflict: bool
    conflicts: List[dict] = Field(default_factory=list, description="冲突详情列表")


class GenerateScheduleRequest(BaseModel):
    """自动排课请求"""
    plan_id: int = Field(..., description="排课方案ID")
    academic_year_id: int = Field(..., description="学年ID")
    semester_id: int = Field(..., description="学期ID")


class GenerateScheduleResponse(BaseModel):
    """自动排课响应"""
    success: bool
    message: str
    total_entries: int = 0
    conflict_count: int = 0
