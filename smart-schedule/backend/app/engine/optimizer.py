"""
排课优化模块

在初始排课完成后，对课表进行进一步优化：
1. 均匀分布：同一科目尽量分散在不同天
2. 减少空课：教师课表尽量集中
3. 主科上午：主科优先安排在上午
4. 连排优化：需要连排的科目安排在相邻节次
5. 小课跟随：语数外后面安排对应小课
"""
import random
from collections import defaultdict
from datetime import time
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.timetable import TimetableEntry, SchedulePlan
from app.models.schedule import ScheduleTemplate, TimeSlot
from app.models.subject import Subject
from app.engine.conflict import has_any_conflict, check_all_conflicts


class ScheduleOptimizer:
    """课表优化器"""

    def __init__(self, db: Session):
        self.db = db

    def optimize(
        self,
        plan: SchedulePlan,
        templates: List[ScheduleTemplate],
        max_rounds: int = 5,
    ) -> Dict:
        """
        执行课表优化

        Args:
            plan: 排课方案
            templates: 作息时间模板列表
            max_rounds: 最大优化轮数

        Returns:
            优化结果统计
        """
        entries = self.db.query(TimetableEntry).filter(
            TimetableEntry.schedule_plan_id == plan.id,
            TimetableEntry.is_locked == False,
        ).all()

        if not entries:
            return {"improved": 0, "rounds": 0}

        total_improved = 0

        for round_num in range(max_rounds):
            improved = self._optimize_round(plan, entries, templates)
            total_improved += improved
            if improved == 0:
                break  # 无法进一步优化

        return {"improved": total_improved, "rounds": round_num + 1}

    def _optimize_round(
        self,
        plan: SchedulePlan,
        entries: List[TimetableEntry],
        templates: List[ScheduleTemplate],
    ) -> int:
        """执行一轮优化，返回改进次数"""
        improved = 0
        random.shuffle(entries)

        for entry in entries:
            # 计算当前位置评分
            current_score = self._score_entry(entry, entries)

            # 获取可用的时间段
            template = self._get_template_for_entry(entry, templates)
            if not template:
                continue

            available_slots = [
                s for s in template.time_slots
                if s.period_type == "上课"
                and not (s.day_of_week == entry.day_of_week and s.period_number == entry.period_number)
            ]

            best_score = current_score
            best_slot = None

            for slot in available_slots:
                # 检查移动后是否冲突
                if has_any_conflict(
                    self.db,
                    teacher_id=entry.teacher_id,
                    class_group_id=entry.class_group_id,
                    classroom_id=entry.classroom_id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    odd_even_type=entry.odd_even_type,
                    schedule_plan_id=plan.id,
                    exclude_entry_id=entry.id,
                ):
                    continue

                # 临时修改并评分
                old_day = entry.day_of_week
                old_period = entry.period_number
                old_start = entry.start_time
                old_end = entry.end_time

                entry.day_of_week = slot.day_of_week
                entry.period_number = slot.period_number
                entry.start_time = slot.start_time
                entry.end_time = slot.end_time

                new_score = self._score_entry(entry, entries)

                # 恢复
                entry.day_of_week = old_day
                entry.period_number = old_period
                entry.start_time = old_start
                entry.end_time = old_end

                if new_score > best_score + 0.3:
                    best_score = new_score
                    best_slot = slot

            # 执行最佳移动
            if best_slot:
                entry.day_of_week = best_slot.day_of_week
                entry.period_number = best_slot.period_number
                entry.start_time = best_slot.start_time
                entry.end_time = best_slot.end_time
                improved += 1

        if improved > 0:
            self.db.flush()

        return improved

    def _score_entry(self, entry: TimetableEntry, all_entries: List[TimetableEntry]) -> float:
        """
        评估单个条目的位置质量

        评分维度：
        1. 科目分布均匀性 (+/-)
        2. 主科上午偏好 (+/-)
        3. 教师课表集中度 (+)
        4. 班级课表均匀性 (+)
        """
        score = 0.0

        # 获取科目信息
        subject = self.db.query(Subject).filter(Subject.id == entry.subject_id).first()
        if not subject:
            return score

        # 1. 科目分布均匀性：同一天同班同科目越少越好
        same_day_same_subject = sum(
            1 for e in all_entries
            if e.subject_id == entry.subject_id
            and e.class_group_id == entry.class_group_id
            and e.day_of_week == entry.day_of_week
            and e.id != entry.id
        )
        score -= same_day_same_subject * 3.0

        # 2. 主科上午偏好
        if subject.subject_type == "主科":
            if entry.start_time.hour < 12:
                score += 2.0
            else:
                score -= 1.5

        # 3. 副科下午偏好
        if subject.subject_type == "副科":
            if entry.start_time.hour >= 12:
                score += 0.5

        # 4. 教师课表集中度：同一天已有课加分（但不超过4节）
        teacher_same_day = sum(
            1 for e in all_entries
            if e.teacher_id == entry.teacher_id
            and e.day_of_week == entry.day_of_week
            and e.id != entry.id
        )
        if 0 < teacher_same_day < 4:
            score += 0.5
        elif teacher_same_day >= 4:
            score -= 1.0

        # 5. 班级课表均匀性
        class_same_day = sum(
            1 for e in all_entries
            if e.class_group_id == entry.class_group_id
            and e.day_of_week == entry.day_of_week
            and e.id != entry.id
        )
        if class_same_day < 3:
            score += 0.3
        elif class_same_day > 5:
            score -= 0.5

        return score

    def _get_template_for_entry(
        self, entry: TimetableEntry, templates: List[ScheduleTemplate]
    ) -> Optional[ScheduleTemplate]:
        """获取条目对应的作息时间模板"""
        for t in templates:
            if t.id == entry.schedule_template_id:
                return t
        return None
