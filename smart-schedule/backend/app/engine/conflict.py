"""
冲突检测模块 (核心模块)

本模块实现了基于实际时间的冲突检测，而非基于节次编号。
这是排课系统最关键的模块，确保教师、班级、教室不会在同一时间段被重复安排。

关键设计：
1. 使用 start_time/end_time 进行时间重叠判断，而非 period_number
2. 支持单双周：单周课和双周课在同一时间段不冲突
3. 所有检测函数都支持 exclude_entry_id 参数，用于编辑时排除自身
"""
from datetime import time, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.models.timetable import TimetableEntry


def times_overlap(
    start1: time, end1: time,
    start2: time, end2: time,
) -> bool:
    """
    判断两个时间段是否重叠

    核心逻辑：两个时间段 [s1, e1) 和 [s2, e2) 重叠的条件是：
    s1 < e2 且 s2 < e1

    注意：这里使用开区间，即相邻但不重叠的时间段不算冲突
    例如 8:00-8:45 和 8:45-9:30 不算冲突

    Args:
        start1: 第一个时间段的开始时间
        end1: 第一个时间段的结束时间
        start2: 第二个时间段的开始时间
        end2: 第二个时间段的结束时间

    Returns:
        True 如果两个时间段重叠，False 否
    """
    # 转换为秒数便于比较
    s1 = start1.hour * 3600 + start1.minute * 60 + start1.second
    e1 = end1.hour * 3600 + end1.minute * 60 + end1.second
    s2 = start2.hour * 3600 + start2.minute * 60 + start2.second
    e2 = end2.hour * 3600 + end2.minute * 60 + end2.second

    # 两个时间段重叠条件：s1 < e2 且 s2 < e1
    return s1 < e2 and s2 < e1


def odd_even_conflicts(type1: str, type2: str) -> bool:
    """
    判断两个单双周类型是否会产生冲突

    规则：
    - all 与 all 冲突（每周都上的课）
    - all 与 odd 冲突（每周的课与单周的课在单周冲突）
    - all 与 even 冲突（每周的课与双周的课在双周冲突）
    - odd 与 odd 冲突（两个单周课冲突）
    - even 与 even 冲突（两个双周课冲突）
    - odd 与 even 不冲突（单周和双周课不在同一周）

    Args:
        type1: 第一个条目的单双周类型 (all/odd/even)
        type2: 第二个条目的单双周类型 (all/odd/even)

    Returns:
        True 如果两种类型在同一周会冲突，False 否
    """
    # 单周和双周互不冲突
    if (type1 == "odd" and type2 == "even") or (type1 == "even" and type2 == "odd"):
        return False
    # 其他情况都冲突
    return True


def check_teacher_conflict(
    db: Session,
    teacher_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    odd_even_type: str,
    schedule_plan_id: int,
    exclude_entry_id: Optional[int] = None,
) -> List[TimetableEntry]:
    """
    检查教师在指定时间段是否有冲突

    核心冲突检测逻辑：
    1. 查找同一排课方案中，同一教师，同一天的所有课表条目
    2. 对每个条目，判断时间是否重叠
    3. 对每个条目，判断单双周是否冲突
    4. 排除自身（编辑场景）

    Args:
        db: 数据库会话
        teacher_id: 教师ID
        day_of_week: 星期几 (1-7)
        start_time: 开始时间
        end_time: 结束时间
        odd_even_type: 单双周类型 (all/odd/even)
        schedule_plan_id: 排课方案ID
        exclude_entry_id: 需要排除的条目ID（编辑时排除自身）

    Returns:
        冲突的课表条目列表，空列表表示无冲突
    """
    # 查询该教师当天所有课表条目
    query = db.query(TimetableEntry).filter(
        TimetableEntry.schedule_plan_id == schedule_plan_id,
        TimetableEntry.teacher_id == teacher_id,
        TimetableEntry.day_of_week == day_of_week,
    )

    # 排除指定条目
    if exclude_entry_id is not None:
        query = query.filter(TimetableEntry.id != exclude_entry_id)

    existing_entries = query.all()

    # 逐一检查时间冲突
    conflicts = []
    for entry in existing_entries:
        # 先检查时间是否重叠
        if times_overlap(start_time, end_time, entry.start_time, entry.end_time):
            # 再检查单双周是否冲突
            if odd_even_conflicts(odd_even_type, entry.odd_even_type):
                conflicts.append(entry)

    return conflicts


def check_class_conflict(
    db: Session,
    class_group_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    odd_even_type: str,
    schedule_plan_id: int,
    exclude_entry_id: Optional[int] = None,
) -> List[TimetableEntry]:
    """
    检查班级在指定时间段是否有冲突

    逻辑与 check_teacher_conflict 类似，但检查对象是班级

    Args:
        db: 数据库会话
        class_group_id: 班级ID
        day_of_week: 星期几 (1-7)
        start_time: 开始时间
        end_time: 结束时间
        odd_even_type: 单双周类型
        schedule_plan_id: 排课方案ID
        exclude_entry_id: 需要排除的条目ID

    Returns:
        冲突的课表条目列表
    """
    query = db.query(TimetableEntry).filter(
        TimetableEntry.schedule_plan_id == schedule_plan_id,
        TimetableEntry.class_group_id == class_group_id,
        TimetableEntry.day_of_week == day_of_week,
    )

    if exclude_entry_id is not None:
        query = query.filter(TimetableEntry.id != exclude_entry_id)

    existing_entries = query.all()

    conflicts = []
    for entry in existing_entries:
        if times_overlap(start_time, end_time, entry.start_time, entry.end_time):
            if odd_even_conflicts(odd_even_type, entry.odd_even_type):
                conflicts.append(entry)

    return conflicts


def check_classroom_conflict(
    db: Session,
    classroom_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    odd_even_type: str,
    schedule_plan_id: int,
    exclude_entry_id: Optional[int] = None,
) -> List[TimetableEntry]:
    """
    检查教室在指定时间段是否有冲突

    逻辑与 check_teacher_conflict 类似，但检查对象是教室
    注意：classroom_id 可能为 None（未分配教室），此时不做教室冲突检测

    Args:
        db: 数据库会话
        classroom_id: 教室ID
        day_of_week: 星期几 (1-7)
        start_time: 开始时间
        end_time: 结束时间
        odd_even_type: 单双周类型
        schedule_plan_id: 排课方案ID
        exclude_entry_id: 需要排除的条目ID

    Returns:
        冲突的课表条目列表
    """
    if classroom_id is None:
        return []

    query = db.query(TimetableEntry).filter(
        TimetableEntry.schedule_plan_id == schedule_plan_id,
        TimetableEntry.classroom_id == classroom_id,
        TimetableEntry.day_of_week == day_of_week,
    )

    if exclude_entry_id is not None:
        query = query.filter(TimetableEntry.id != exclude_entry_id)

    existing_entries = query.all()

    conflicts = []
    for entry in existing_entries:
        if times_overlap(start_time, end_time, entry.start_time, entry.end_time):
            if odd_even_conflicts(odd_even_type, entry.odd_even_type):
                conflicts.append(entry)

    return conflicts


def check_all_conflicts(
    db: Session,
    teacher_id: int,
    class_group_id: int,
    classroom_id: Optional[int],
    day_of_week: int,
    start_time: time,
    end_time: time,
    odd_even_type: str,
    schedule_plan_id: int,
    exclude_entry_id: Optional[int] = None,
) -> Dict[str, List[TimetableEntry]]:
    """
    综合检查所有冲突（教师+班级+教室）

    这是最常用的冲突检测入口，一次性返回所有类型的冲突

    Args:
        db: 数据库会话
        teacher_id: 教师ID
        class_group_id: 班级ID
        classroom_id: 教室ID（可选）
        day_of_week: 星期几
        start_time: 开始时间
        end_time: 结束时间
        odd_even_type: 单双周类型
        schedule_plan_id: 排课方案ID
        exclude_entry_id: 需要排除的条目ID

    Returns:
        字典，包含三种冲突类型：
        {
            "teacher": [...],   # 教师冲突
            "class": [...],     # 班级冲突
            "classroom": [...], # 教室冲突
        }
    """
    result: Dict[str, List[TimetableEntry]] = {
        "teacher": [],
        "class": [],
        "classroom": [],
    }

    # 检查教师冲突
    result["teacher"] = check_teacher_conflict(
        db, teacher_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    )

    # 检查班级冲突
    result["class"] = check_class_conflict(
        db, class_group_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    )

    # 检查教室冲突
    result["classroom"] = check_classroom_conflict(
        db, classroom_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    )

    return result


def has_any_conflict(
    db: Session,
    teacher_id: int,
    class_group_id: int,
    classroom_id: Optional[int],
    day_of_week: int,
    start_time: time,
    end_time: time,
    odd_even_type: str,
    schedule_plan_id: int,
    exclude_entry_id: Optional[int] = None,
) -> bool:
    """
    快速判断是否存在任何冲突

    比 check_all_conflicts 更高效，找到第一个冲突即返回

    Returns:
        True 如果存在任何冲突
    """
    # 按优先级检查：教师冲突最严重，先检查
    if check_teacher_conflict(
        db, teacher_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    ):
        return True

    # 班级冲突
    if check_class_conflict(
        db, class_group_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    ):
        return True

    # 教室冲突
    if classroom_id and check_classroom_conflict(
        db, classroom_id, day_of_week, start_time, end_time,
        odd_even_type, schedule_plan_id, exclude_entry_id
    ):
        return True

    return False
