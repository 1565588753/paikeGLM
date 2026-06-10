"""
班级相关的 Pydantic Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ClassGroupCreate(BaseModel):
    """创建班级请求"""
    name: str = Field(..., max_length=50, description="班级名称")
    short_name: Optional[str] = Field(None, max_length=20, description="班级简称")
    grade_id: int = Field(..., description="年级ID")
    student_count: int = Field(0, ge=0, description="学生人数")
    head_teacher_id: Optional[int] = Field(None, description="班主任ID")
    class_type: str = Field("普通班", description="班级类型")
    academic_year_id: int = Field(..., description="学年ID")


class ClassGroupUpdate(BaseModel):
    """更新班级请求"""
    name: Optional[str] = Field(None, max_length=50, description="班级名称")
    short_name: Optional[str] = Field(None, max_length=20, description="班级简称")
    student_count: Optional[int] = Field(None, ge=0, description="学生人数")
    head_teacher_id: Optional[int] = Field(None, description="班主任ID")
    class_type: Optional[str] = Field(None, description="班级类型")


class ClassGroupImport(BaseModel):
    """批量导入班级"""
    classes: List[ClassGroupCreate]


class ClassGroupResponse(BaseModel):
    """班级响应"""
    id: int
    name: str
    short_name: Optional[str] = None
    grade_id: int
    student_count: int
    head_teacher_id: Optional[int] = None
    class_type: str
    academic_year_id: int
    # 关联信息
    grade_name: Optional[str] = None
    head_teacher_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ClassGroupListResponse(BaseModel):
    """班级列表响应"""
    items: List[ClassGroupResponse]
    total: int
    page: int
    page_size: int
