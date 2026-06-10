"""
约束定义模块

定义排课过程中需要满足的各种约束条件：
1. 硬约束 (Hard Constraints) - 必须满足，违反则排课失败
2. 软约束 (Soft Constraints) - 尽量满足，违反则降低排课质量
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import time


@dataclass
class ConstraintViolation:
    """约束违反记录"""
    constraint_name: str           # 约束名称
    severity: str                  # 严重程度: hard/soft
    description: str               # 违反描述
    affected_entries: List[int] = field(default_factory=list)  # 受影响的条目ID列表


@dataclass
class SubjectConstraints:
    """科目约束 - 来自 Subject 模型的排课约束"""
    subject_id: int
    subject_name: str
    max_per_day: int = 2           # 每天最大课时数
    max_per_week: int = 10         # 每周最大课时数
    allow_consecutive: bool = False # 是否允许连排
    max_consecutive: int = 2       # 最大连排节数
    needs_special_room: bool = False # 是否需要专用教室
    priority: int = 5              # 优先级
    supports_odd_even: bool = False # 是否支持单双周


@dataclass
class TeacherConstraints:
    """教师约束"""
    teacher_id: int
    teacher_name: str
    # 教师不可用的时间段 (day_of_week, period_number) 集合
    unavailable_slots: Set[Tuple[int, int]] = field(default_factory=set)
    # 教师每天最大课时数
    max_per_day: int = 6
    # 教师偏好上午还是下午
    prefer_morning: bool = False
    prefer_afternoon: bool = False


@dataclass
class ClassConstraints:
    """班级约束"""
    class_group_id: int
    class_name: str
    # 班级每天最大课时数
    max_per_day: int = 8
    # 班级是否需要固定教室
    fixed_classroom_id: Optional[int] = None


@dataclass
class ScheduleConstraints:
    """
    排课约束集合 - 包含一次排课的所有约束条件

    硬约束（必须满足）：
    1. 教师同一时间只能上一门课
    2. 班级同一时间只能上一门课
    3. 教室同一时间只能安排一门课
    4. 预排课程必须固定
    5. 科目每天不超过最大课时数
    6. 科目每周不超过最大课时数

    软约束（尽量满足）：
    1. 主科优先安排在上午
    2. 同一科目尽量分散在不同天
    3. 连排课尽量安排在相邻节次
    4. 教师课表尽量集中，减少空课
    5. 班级课表尽量均匀分布
    6. 语数外后面尽量安排对应小课
    """
    # 科目约束映射
    subject_constraints: Dict[int, SubjectConstraints] = field(default_factory=dict)
    # 教师约束映射
    teacher_constraints: Dict[int, TeacherConstraints] = field(default_factory=dict)
    # 班级约束映射
    class_constraints: Dict[int, ClassConstraints] = field(default_factory=dict)
    # 预排课程 (teaching_assignment_id -> [(day_of_week, period_number)])
    pre_scheduled: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)
    # 主科-小课映射 (主科ID -> 小课ID列表)
    subject_sub_mappings: Dict[int, List[int]] = field(default_factory=dict)
    # 每周天数
    days_per_week: int = 5
    # 每天最大节数
    max_periods_per_day: int = 8


def check_hard_constraint_max_per_day(
    subject_id: int,
    day_of_week: int,
    current_count: int,
    constraints: SubjectConstraints,
) -> Optional[ConstraintViolation]:
    """
    检查科目每天最大课时数约束（硬约束）

    Args:
        subject_id: 科目ID
        day_of_week: 星期几
        current_count: 当天已安排的课时数
        constraints: 科目约束

    Returns:
        如果违反约束返回 ConstraintViolation，否则返回 None
    """
    if current_count >= constraints.max_per_day:
        return ConstraintViolation(
            constraint_name="max_per_day",
            severity="hard",
            description=f"科目 {constraints.subject_name} 在星期{day_of_week}已达到每天最大课时数 {constraints.max_per_day}",
        )
    return None


def check_hard_constraint_max_per_week(
    subject_id: int,
    current_count: int,
    constraints: SubjectConstraints,
) -> Optional[ConstraintViolation]:
    """
    检查科目每周最大课时数约束（硬约束）
    """
    if current_count >= constraints.max_per_week:
        return ConstraintViolation(
            constraint_name="max_per_week",
            severity="hard",
            description=f"科目 {constraints.subject_name} 已达到每周最大课时数 {constraints.max_per_week}",
        )
    return None


def check_soft_constraint_subject_distribution(
    subject_id: int,
    day_of_week: int,
    existing_days: List[int],
    constraints: SubjectConstraints,
) -> Optional[ConstraintViolation]:
    """
    检查科目分布均匀性（软约束）

    同一科目尽量分散在不同天，避免同一天上多节
    """
    if day_of_week in existing_days and len(existing_days) > 0:
        return ConstraintViolation(
            constraint_name="subject_distribution",
            severity="soft",
            description=f"科目 {constraints.subject_name} 在星期{day_of_week}已有安排，建议分散到其他天",
        )
    return None


def check_soft_constraint_morning_priority(
    subject_id: int,
    is_morning: bool,
    constraints: SubjectConstraints,
) -> Optional[ConstraintViolation]:
    """
    检查主科上午优先约束（软约束）

    主科（语文、数学、英语等）优先安排在上午
    """
    if constraints.subject_type == "主科" and not is_morning:
        return ConstraintViolation(
            constraint_name="morning_priority",
            severity="soft",
            description=f"主科 {constraints.subject_name} 建议安排在上午",
        )
    return None


def check_soft_constraint_consecutive(
    subject_id: int,
    day_of_week: int,
    period_number: int,
    existing_periods: List[Tuple[int, int]],
    constraints: SubjectConstraints,
) -> Optional[ConstraintViolation]:
    """
    检查连排约束（软约束）

    如果科目不允许连排，则同一天不应有相邻节次
    如果科目允许连排，则连排节数不应超过最大值
    """
    same_day_periods = [p for d, p in existing_periods if d == day_of_week]

    if not constraints.allow_consecutive and same_day_periods:
        # 不允许连排但同天已有课
        for p in same_day_periods:
            if abs(p - period_number) == 1:
                return ConstraintViolation(
                    constraint_name="no_consecutive",
                    severity="soft",
                    description=f"科目 {constraints.subject_name} 不允许连排",
                )

    if constraints.allow_consecutive and same_day_periods:
        # 允许连排但检查最大连排数
        consecutive_count = 1
        sorted_periods = sorted(same_day_periods + [period_number])
        for i in range(1, len(sorted_periods)):
            if sorted_periods[i] - sorted_periods[i - 1] == 1:
                consecutive_count += 1
                if consecutive_count > constraints.max_consecutive:
                    return ConstraintViolation(
                        constraint_name="max_consecutive",
                        severity="soft",
                        description=f"科目 {constraints.subject_name} 连排数超过最大值 {constraints.max_consecutive}",
                    )
            else:
                consecutive_count = 1

    return None
