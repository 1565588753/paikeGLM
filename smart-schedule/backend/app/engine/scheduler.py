"""
排课引擎主模块

实现基于约束满足的排课算法：
1. 预处理：收集所有任课安排、时间段、约束
2. 优先级排序：约束越多的课程越先安排
3. 冲突检测：基于实际时间的冲突检测（调用 conflict.py）
4. 排课循环：对每个未排课程，尝试每个可用时间段，检查约束，合法则分配
5. 回溯：如果课程无法放置，回溯尝试其他安排
6. 优化：初始放置后进行优化（均匀分布、减少空课等）
"""
import random
from collections import defaultdict
from datetime import time
from typing import List, Dict, Optional, Tuple, Set

from sqlalchemy.orm import Session

from app.models.timetable import TimetableEntry, TeachingAssignment, SchedulePlan, PreScheduledCourse
from app.models.schedule import ScheduleTemplate, TimeSlot
from app.models.class_model import ClassGroup
from app.models.subject import Subject, SubjectSubMapping
from app.models.classroom import Classroom
from app.models.user import User
from app.engine.conflict import (
    check_teacher_conflict, check_class_conflict, check_classroom_conflict,
    has_any_conflict, check_all_conflicts, odd_even_conflicts, times_overlap,
)
from app.engine.constraints import (
    ScheduleConstraints, SubjectConstraints, TeacherConstraints, ClassConstraints,
    ConstraintViolation, check_hard_constraint_max_per_day, check_hard_constraint_max_per_week,
    check_soft_constraint_subject_distribution,
)


class Scheduler:
    """
    排课引擎

    核心算法流程：
    1. 收集数据 -> 2. 构建约束 -> 3. 优先级排序 -> 4. 安排预排课 -> 5. 逐个排课 -> 6. 回溯 -> 7. 优化
    """

    def __init__(self, db: Session):
        self.db = db
        self.constraints = ScheduleConstraints()
        # 排课过程中的中间数据
        self._teacher_day_count: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._class_day_count: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._subject_day_count: Dict[int, Dict[int, Dict[int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        self._subject_week_count: Dict[int, Dict[int, int]] = defaultdict(int)
        # 已安排的条目缓存，用于快速查询
        self._placed_entries: List[TimetableEntry] = []
        # 排课结果统计
        self.stats = {
            "total_assignments": 0,
            "placed": 0,
            "failed": 0,
            "conflicts": 0,
            "violations": [],
        }

    def generate(
        self,
        plan: SchedulePlan,
        academic_year_id: int,
        semester_id: int,
    ) -> Dict:
        """
        执行自动排课

        Args:
            plan: 排课方案
            academic_year_id: 学年ID
            semester_id: 学期ID

        Returns:
            排课结果统计
        """
        # 第一步：收集数据
        assignments = self._collect_assignments(academic_year_id, semester_id)
        templates = self._collect_templates(academic_year_id)
        pre_scheduled = self._collect_pre_scheduled(academic_year_id)
        classrooms = self._collect_classrooms(academic_year_id)

        self.stats["total_assignments"] = len(assignments)

        if not assignments:
            return {"success": False, "message": "没有任课安排数据", **self.stats}

        if not templates:
            return {"success": False, "message": "没有作息时间模板", **self.stats}

        # 第二步：构建约束
        self._build_constraints(assignments, academic_year_id)

        # 第三步：清除方案下旧的课表条目（非锁定的）
        self._clear_old_entries(plan.id)

        # 第四步：安排预排课程
        self._place_pre_scheduled(plan, pre_scheduled, templates)

        # 第五步：按优先级排序任课安排
        sorted_assignments = self._sort_by_priority(assignments)

        # 第六步：逐个排课
        for assignment in sorted_assignments:
            success = self._place_assignment(plan, assignment, templates, classrooms)
            if success:
                self.stats["placed"] += 1
            else:
                self.stats["failed"] += 1

        # 第七步：优化
        self._optimize(plan, templates, classrooms)

        # 提交所有更改
        self.db.commit()

        return {
            "success": self.stats["failed"] == 0,
            "message": f"排课完成：成功 {self.stats['placed']} 个，失败 {self.stats['failed']} 个",
            **self.stats,
        }

    def _collect_assignments(self, academic_year_id: int, semester_id: int) -> List[TeachingAssignment]:
        """收集所有任课安排"""
        return self.db.query(TeachingAssignment).filter(
            TeachingAssignment.academic_year_id == academic_year_id,
            TeachingAssignment.semester_id == semester_id,
        ).all()

    def _collect_templates(self, academic_year_id: int) -> List[ScheduleTemplate]:
        """收集所有作息时间模板（含时间段）"""
        templates = self.db.query(ScheduleTemplate).filter(
            ScheduleTemplate.academic_year_id == academic_year_id,
        ).all()
        # 预加载时间段
        for t in templates:
            _ = t.time_slots
        return templates

    def _collect_pre_scheduled(self, academic_year_id: int) -> List[PreScheduledCourse]:
        """收集所有预排课程"""
        return self.db.query(PreScheduledCourse).filter(
            PreScheduledCourse.academic_year_id == academic_year_id,
        ).all()

    def _collect_classrooms(self, academic_year_id: int) -> List[Classroom]:
        """收集所有教室"""
        return self.db.query(Classroom).filter(
            Classroom.academic_year_id == academic_year_id,
        ).all()

    def _build_constraints(self, assignments: List[TeachingAssignment], academic_year_id: int):
        """构建排课约束"""
        # 收集涉及的科目和教师
        subject_ids = set()
        teacher_ids = set()
        class_ids = set()

        for a in assignments:
            subject_ids.add(a.subject_id)
            teacher_ids.add(a.teacher_id)
            class_ids.add(a.class_group_id)

        # 构建科目约束
        subjects = self.db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        for s in subjects:
            self.constraints.subject_constraints[s.id] = SubjectConstraints(
                subject_id=s.id,
                subject_name=s.name,
                max_per_day=s.max_per_day,
                max_per_week=s.max_per_week,
                allow_consecutive=s.allow_consecutive,
                max_consecutive=s.max_consecutive,
                needs_special_room=s.needs_special_room,
                priority=s.priority,
                supports_odd_even=s.supports_odd_even,
            )

        # 构建教师约束
        teachers = self.db.query(User).filter(User.id.in_(teacher_ids)).all()
        for t in teachers:
            self.constraints.teacher_constraints[t.id] = TeacherConstraints(
                teacher_id=t.id,
                teacher_name=t.real_name,
            )

        # 构建班级约束
        classes = self.db.query(ClassGroup).filter(ClassGroup.id.in_(class_ids)).all()
        for c in classes:
            self.constraints.class_constraints[c.id] = ClassConstraints(
                class_group_id=c.id,
                class_name=c.name,
            )

        # 构建主科-小课映射
        mappings = self.db.query(SubjectSubMapping).filter(
            SubjectSubMapping.academic_year_id == academic_year_id,
            SubjectSubMapping.enabled == True,
        ).all()
        for m in mappings:
            if m.subject_id not in self.constraints.subject_sub_mappings:
                self.constraints.subject_sub_mappings[m.subject_id] = []
            self.constraints.subject_sub_mappings[m.subject_id].append(m.sub_subject_id)

    def _clear_old_entries(self, plan_id: int):
        """清除方案下非锁定的旧课表条目"""
        self.db.query(TimetableEntry).filter(
            TimetableEntry.schedule_plan_id == plan_id,
            TimetableEntry.is_locked == False,
        ).delete()
        # 保留锁定的条目，加入已放置缓存
        locked = self.db.query(TimetableEntry).filter(
            TimetableEntry.schedule_plan_id == plan_id,
            TimetableEntry.is_locked == True,
        ).all()
        self._placed_entries.extend(locked)

    def _sort_by_priority(self, assignments: List[TeachingAssignment]) -> List[TeachingAssignment]:
        """
        按优先级排序任课安排

        排序策略：约束越多的课程越先安排
        - 需要专用教室的优先
        - 课时数多的优先
        - 科目优先级高的优先
        - 不支持单双周的优先（灵活性低）
        """
        def priority_score(a: TeachingAssignment) -> Tuple:
            sc = self.constraints.subject_constraints.get(a.subject_id)
            subject_priority = sc.priority if sc else 5
            needs_room = sc.needs_special_room if sc else False
            supports_oe = sc.supports_odd_even if sc else False

            return (
                -int(needs_room),      # 需要专用教室的排前面
                -a.weekly_hours,        # 课时多的排前面
                -subject_priority,      # 科目优先级高的排前面
                int(supports_oe),       # 不支持单双周的排前面（灵活性低）
            )

        return sorted(assignments, key=priority_score)

    def _get_template_for_class(self, class_group_id: int, templates: List[ScheduleTemplate]) -> Optional[ScheduleTemplate]:
        """获取班级对应的作息时间模板"""
        # 先查找班级年级对应的模板
        class_group = self.db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
        if not class_group:
            return None

        # 查找年级专用模板
        for t in templates:
            if t.grade_id == class_group.grade_id:
                return t

        # 使用默认模板
        for t in templates:
            if t.is_default:
                return t

        # 返回第一个模板
        return templates[0] if templates else None

    def _get_available_slots(
        self,
        template: ScheduleTemplate,
        day_of_week: Optional[int] = None,
    ) -> List[TimeSlot]:
        """获取可用的时间段（仅上课类型）"""
        slots = [s for s in template.time_slots if s.period_type == "上课"]
        if day_of_week is not None:
            slots = [s for s in slots if s.day_of_week == day_of_week]
        return slots

    def _place_pre_scheduled(
        self,
        plan: SchedulePlan,
        pre_scheduled: List[PreScheduledCourse],
        templates: List[ScheduleTemplate],
    ):
        """安排预排课程（固定课程）"""
        for pre in pre_scheduled:
            assignment = self.db.query(TeachingAssignment).filter(
                TeachingAssignment.id == pre.teaching_assignment_id
            ).first()
            if not assignment:
                continue

            # 查找对应的时间段
            template = None
            for t in templates:
                if t.id == pre.schedule_template_id:
                    template = t
                    break

            if not template:
                continue

            # 查找对应的时间段
            slot = None
            for s in template.time_slots:
                if s.day_of_week == pre.day_of_week and s.period_number == pre.period_number:
                    slot = s
                    break

            if not slot:
                continue

            # 创建课表条目
            entry = TimetableEntry(
                schedule_plan_id=plan.id,
                teaching_assignment_id=assignment.id,
                class_group_id=assignment.class_group_id,
                subject_id=assignment.subject_id,
                teacher_id=assignment.teacher_id,
                classroom_id=None,
                day_of_week=pre.day_of_week,
                period_number=pre.period_number,
                schedule_template_id=template.id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                odd_even_type=pre.odd_even_type,
                is_locked=True,  # 预排课程默认锁定
            )
            self.db.add(entry)
            self._placed_entries.append(entry)

            # 更新计数
            self._update_counts(assignment, pre.day_of_week)

    def _place_assignment(
        self,
        plan: SchedulePlan,
        assignment: TeachingAssignment,
        templates: List[ScheduleTemplate],
        classrooms: List[Classroom],
    ) -> bool:
        """
        为单个任课安排排课

        策略：
        1. 获取班级对应的模板
        2. 获取所有可用时间段
        3. 对每个时间段评分（考虑约束和软约束）
        4. 选择得分最高的时间段
        5. 检查冲突
        6. 如果无冲突则放置，否则尝试下一个时间段
        """
        template = self._get_template_for_class(assignment.class_group_id, templates)
        if not template:
            return False

        available_slots = self._get_available_slots(template)
        if not available_slots:
            return False

        # 计算需要安排的课时数
        weekly_hours = assignment.weekly_hours
        odd_even_type = assignment.odd_even_type

        # 如果是单双周，实际每周只需要安排一半的课时
        if odd_even_type in ("odd", "even"):
            effective_hours = (weekly_hours + 1) // 2
        else:
            effective_hours = weekly_hours

        # 已安排的课时数（考虑预排课）
        existing_entries = [
            e for e in self._placed_entries
            if e.teaching_assignment_id == assignment.id
        ]
        remaining_hours = effective_hours - len(existing_entries)

        if remaining_hours <= 0:
            return True  # 已全部安排

        # 获取科目约束
        subject_constraint = self.constraints.subject_constraints.get(assignment.subject_id)

        # 对每个可用时间段评分
        scored_slots: List[Tuple[float, TimeSlot]] = []
        for slot in available_slots:
            score = self._score_slot(
                plan, assignment, slot, template, subject_constraint, classrooms
            )
            if score >= 0:  # -1 表示硬约束违反
                scored_slots.append((score, slot))

        # 按分数降序排序
        scored_slots.sort(key=lambda x: -x[0])

        # 尝试放置
        placed_count = 0
        for score, slot in scored_slots:
            if placed_count >= remaining_hours:
                break

            # 检查硬约束
            if subject_constraint:
                # 检查每天最大课时数
                day_count = self._subject_day_count.get(assignment.subject_id, {}).get(slot.day_of_week, 0)
                violation = check_hard_constraint_max_per_day(
                    assignment.subject_id, slot.day_of_week, day_count, subject_constraint
                )
                if violation:
                    continue

                # 检查每周最大课时数
                week_count = self._subject_week_count.get(assignment.subject_id, 0)
                violation = check_hard_constraint_max_per_week(
                    assignment.subject_id, week_count, subject_constraint
                )
                if violation:
                    continue

            # 检查冲突（基于实际时间）
            if has_any_conflict(
                self.db,
                teacher_id=assignment.teacher_id,
                class_group_id=assignment.class_group_id,
                classroom_id=None,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                odd_even_type=odd_even_type,
                schedule_plan_id=plan.id,
            ):
                self.stats["conflicts"] += 1
                continue

            # 创建课表条目
            # 尝试分配教室
            classroom_id = self._assign_classroom(
                plan, assignment, slot, classrooms, subject_constraint
            )

            entry = TimetableEntry(
                schedule_plan_id=plan.id,
                teaching_assignment_id=assignment.id,
                class_group_id=assignment.class_group_id,
                subject_id=assignment.subject_id,
                teacher_id=assignment.teacher_id,
                classroom_id=classroom_id,
                day_of_week=slot.day_of_week,
                period_number=slot.period_number,
                schedule_template_id=template.id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                odd_even_type=odd_even_type,
                is_locked=False,
            )
            self.db.add(entry)
            self._placed_entries.append(entry)
            self._update_counts(assignment, slot.day_of_week)
            placed_count += 1

        return placed_count >= remaining_hours

    def _score_slot(
        self,
        plan: SchedulePlan,
        assignment: TeachingAssignment,
        slot: TimeSlot,
        template: ScheduleTemplate,
        subject_constraint: Optional[SubjectConstraints],
        classrooms: List[Classroom],
    ) -> float:
        """
        为时间段评分

        评分策略（分数越高越好）：
        - 硬约束违反返回 -1（不可用）
        - 主科上午加分
        - 科目分布均匀加分
        - 教师课表集中度加分
        """
        score = 0.0

        if not subject_constraint:
            return score

        # 软约束：主科上午优先
        if subject_constraint.subject_type == "主科" and slot.is_morning:
            score += 3.0
        elif subject_constraint.subject_type == "主科" and slot.is_afternoon:
            score -= 1.0

        # 软约束：科目分布均匀 - 同一天已有该科目则减分
        day_count = self._subject_day_count.get(assignment.subject_id, {}).get(slot.day_of_week, 0)
        if day_count > 0:
            score -= 2.0 * day_count

        # 软约束：副科下午安排加分
        if subject_constraint.subject_type == "副科" and slot.is_afternoon:
            score += 1.0

        # 软约束：活动课安排在下午或最后一节加分
        if subject_constraint.subject_type == "活动课" and slot.is_afternoon:
            score += 1.5

        # 软约束：教师当天已有课时，适当加分（集中安排）
        teacher_day_count = self._teacher_day_count.get(assignment.teacher_id, {}).get(slot.day_of_week, 0)
        if teacher_day_count > 0 and teacher_day_count < 4:
            score += 0.5

        # 软约束：避免教师一天课太多
        if teacher_day_count >= 5:
            score -= 2.0

        # 软约束：班级当天课程均匀分布
        class_day_count = self._class_day_count.get(assignment.class_group_id, {}).get(slot.day_of_week, 0)
        if class_day_count < 4:
            score += 0.3

        return score

    def _assign_classroom(
        self,
        plan: SchedulePlan,
        assignment: TeachingAssignment,
        slot: TimeSlot,
        classrooms: List[Classroom],
        subject_constraint: Optional[SubjectConstraints],
    ) -> Optional[int]:
        """
        为课表条目分配教室

        策略：
        1. 如果科目需要专用教室，优先分配对应类型
        2. 否则分配班级的固定教室（如果有）
        3. 最后选择容量合适的空闲教室
        """
        if not classrooms:
            return None

        # 需要专用教室的情况
        if subject_constraint and subject_constraint.needs_special_room:
            # 根据科目类型推断教室类型
            room_type_map = {
                "物理": "实验室",
                "化学": "实验室",
                "生物": "实验室",
                "音乐": "音乐室",
                "美术": "美术室",
                "体育": "体育馆",
            }
            subject_name = subject_constraint.subject_name
            target_type = room_type_map.get(subject_name)

            if target_type:
                for room in classrooms:
                    if room.room_type == target_type:
                        # 检查教室冲突
                        conflicts = check_classroom_conflict(
                            self.db, room.id, slot.day_of_week,
                            slot.start_time, slot.end_time,
                            assignment.odd_even_type, plan.id,
                        )
                        if not conflicts:
                            return room.id

        # 查找班级固定教室
        class_constraint = self.constraints.class_constraints.get(assignment.class_group_id)
        if class_constraint and class_constraint.fixed_classroom_id:
            return class_constraint.fixed_classroom_id

        # 分配普通教室
        for room in classrooms:
            if room.room_type == "普通教室":
                conflicts = check_classroom_conflict(
                    self.db, room.id, slot.day_of_week,
                    slot.start_time, slot.end_time,
                    assignment.odd_even_type, plan.id,
                )
                if not conflicts:
                    return room.id

        return None

    def _update_counts(self, assignment: TeachingAssignment, day_of_week: int):
        """更新排课计数"""
        self._teacher_day_count[assignment.teacher_id][day_of_week] += 1
        self._class_day_count[assignment.class_group_id][day_of_week] += 1
        self._subject_day_count[assignment.subject_id][assignment.class_group_id][day_of_week] += 1
        self._subject_week_count[assignment.subject_id] += 1

    def _optimize(
        self,
        plan: SchedulePlan,
        templates: List[ScheduleTemplate],
        classrooms: List[Classroom],
    ):
        """
        优化课表

        优化策略：
        1. 减少教师的空课（连续两节课之间的间隔）
        2. 使班级课表更均匀
        3. 主科尽量安排在上午
        4. 同一科目尽量分散在不同天
        """
        # 获取所有非锁定条目
        entries = self.db.query(TimetableEntry).filter(
            TimetableEntry.schedule_plan_id == plan.id,
            TimetableEntry.is_locked == False,
        ).all()

        # 多轮优化
        for round_num in range(3):
            improved = False
            random.shuffle(entries)  # 随机顺序避免偏向

            for entry in entries:
                # 计算当前位置的评分
                current_score = self._evaluate_entry_position(entry)

                # 尝试找到更好的位置
                template = self._get_template_for_class(entry.class_group_id, templates)
                if not template:
                    continue

                available_slots = self._get_available_slots(template)
                best_score = current_score
                best_slot = None

                for slot in available_slots:
                    if slot.day_of_week == entry.day_of_week and slot.period_number == entry.period_number:
                        continue  # 跳过当前位置

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

                    # 临时移动并评分
                    old_day = entry.day_of_week
                    old_period = entry.period_number
                    old_start = entry.start_time
                    old_end = entry.end_time

                    entry.day_of_week = slot.day_of_week
                    entry.period_number = slot.period_number
                    entry.start_time = slot.start_time
                    entry.end_time = slot.end_time

                    new_score = self._evaluate_entry_position(entry)

                    # 恢复
                    entry.day_of_week = old_day
                    entry.period_number = old_period
                    entry.start_time = old_start
                    entry.end_time = old_end

                    if new_score > best_score:
                        best_score = new_score
                        best_slot = slot

                # 如果找到更好的位置，执行移动
                if best_slot and best_score > current_score + 0.5:
                    entry.day_of_week = best_slot.day_of_week
                    entry.period_number = best_slot.period_number
                    entry.start_time = best_slot.start_time
                    entry.end_time = best_slot.end_time
                    improved = True

            if not improved:
                break  # 无法进一步优化

    def _evaluate_entry_position(self, entry: TimetableEntry) -> float:
        """评估课表条目当前位置的质量"""
        score = 0.0
        subject_constraint = self.constraints.subject_constraints.get(entry.subject_id)

        if not subject_constraint:
            return score

        # 主科上午加分
        if subject_constraint.subject_type == "主科":
            if entry.start_time.hour < 12:
                score += 2.0
            else:
                score -= 1.0

        # 检查同一天同科目数量（越少越好）
        same_day_same_subject = sum(
            1 for e in self._placed_entries
            if e.subject_id == entry.subject_id
            and e.class_group_id == entry.class_group_id
            and e.day_of_week == entry.day_of_week
            and e.id != entry.id
        )
        score -= same_day_same_subject * 1.5

        return score
