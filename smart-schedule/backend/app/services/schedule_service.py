"""
排课服务模块
- 作息时间模板管理
- 时间段管理
- 自动排课
- 课表条目管理（移动、冲突检查）
- 排课方案管理
"""
from datetime import datetime, time
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.models.schedule import ScheduleTemplate, TimeSlot
from app.models.timetable import (
    TimetableEntry, TeachingAssignment, PreScheduledCourse, SchedulePlan
)
from app.models.class_model import ClassGroup
from app.models.subject import Subject
from app.models.classroom import Classroom
from app.models.user import User
from app.engine.scheduler import Scheduler
from app.engine.conflict import check_all_conflicts, has_any_conflict
from app.schemas.schedule import (
    ScheduleTemplateCreate, ScheduleTemplateResponse,
    TimeSlotCreate, TimeSlotBatchUpdate, TimeSlotResponse,
)
from app.schemas.timetable import (
    TimetableEntryResponse, TimetableMoveRequest, ConflictCheckRequest,
    ConflictCheckResponse, GenerateScheduleRequest, GenerateScheduleResponse,
    SchedulePlanCreate, SchedulePlanResponse, TeachingAssignmentCreate,
    TeachingAssignmentResponse, TeachingAssignmentImport,
    PreScheduledCourseCreate, PreScheduledCourseResponse,
)


class ScheduleService:
    """作息时间模板和时间段管理服务"""

    @staticmethod
    def list_templates(
        db: Session, academic_year_id: Optional[int] = None
    ) -> List[ScheduleTemplateResponse]:
        """获取作息时间模板列表"""
        query = db.query(ScheduleTemplate)
        if academic_year_id:
            query = query.filter(ScheduleTemplate.academic_year_id == academic_year_id)

        templates = query.all()
        items = []
        for t in templates:
            resp = ScheduleTemplateResponse.model_validate(t)
            if t.grade:
                resp.grade_name = t.grade.name
            items.append(resp)
        return items

    @staticmethod
    def create_template(db: Session, data: ScheduleTemplateCreate) -> ScheduleTemplateResponse:
        """创建作息时间模板"""
        template = ScheduleTemplate(**data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)

        resp = ScheduleTemplateResponse.model_validate(template)
        if template.grade:
            resp.grade_name = template.grade.name
        return resp

    @staticmethod
    def get_template_slots(db: Session, template_id: int) -> List[TimeSlotResponse]:
        """获取模板的时间段列表"""
        slots = db.query(TimeSlot).filter(
            TimeSlot.schedule_template_id == template_id
        ).order_by(TimeSlot.day_of_week, TimeSlot.period_number).all()

        return [TimeSlotResponse.model_validate(s) for s in slots]

    @staticmethod
    def update_template_slots(
        db: Session, template_id: int, data: TimeSlotBatchUpdate
    ) -> List[TimeSlotResponse]:
        """
        批量更新模板的时间段

        策略：先删除旧的时间段，再创建新的
        """
        # 删除旧的时间段
        db.query(TimeSlot).filter(
            TimeSlot.schedule_template_id == template_id
        ).delete()

        # 创建新的时间段
        new_slots = []
        for slot_data in data.slots:
            slot = TimeSlot(
                schedule_template_id=template_id,
                **slot_data.model_dump(),
            )
            db.add(slot)
            new_slots.append(slot)

        db.commit()

        return [TimeSlotResponse.model_validate(s) for s in new_slots]


class TimetableService:
    """课表管理服务"""

    @staticmethod
    def get_timetable_entries(
        db: Session,
        plan_id: Optional[int] = None,
        class_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        classroom_id: Optional[int] = None,
        odd_even: Optional[str] = None,
    ) -> List[TimetableEntryResponse]:
        """获取课表条目（支持多种筛选条件）"""
        query = db.query(TimetableEntry)

        if plan_id:
            query = query.filter(TimetableEntry.schedule_plan_id == plan_id)
        if class_id:
            query = query.filter(TimetableEntry.class_group_id == class_id)
        if teacher_id:
            query = query.filter(TimetableEntry.teacher_id == teacher_id)
        if classroom_id:
            query = query.filter(TimetableEntry.classroom_id == classroom_id)
        if odd_even and odd_even != "all":
            # 查询所有或指定单双周类型
            query = query.filter(
                (TimetableEntry.odd_even_type == odd_even) |
                (TimetableEntry.odd_even_type == "all")
            )

        entries = query.order_by(
            TimetableEntry.day_of_week, TimetableEntry.period_number
        ).all()

        items = []
        for e in entries:
            resp = TimetableEntryResponse.model_validate(e)
            # 填充关联信息
            if e.class_group:
                resp.class_name = e.class_group.name
            if e.subject:
                resp.subject_name = e.subject.name
                resp.subject_short_name = e.subject.short_name
            if e.teacher:
                resp.teacher_name = e.teacher.real_name
            if e.classroom:
                resp.classroom_name = e.classroom.name
            items.append(resp)

        return items

    @staticmethod
    def generate_schedule(
        db: Session, data: GenerateScheduleRequest
    ) -> GenerateScheduleResponse:
        """
        执行自动排课

        调用排课引擎进行自动排课
        """
        # 获取排课方案
        plan = db.query(SchedulePlan).filter(SchedulePlan.id == data.plan_id).first()
        if not plan:
            raise ValueError("排课方案不存在")

        # 执行排课
        scheduler = Scheduler(db)
        result = scheduler.generate(plan, data.academic_year_id, data.semester_id)

        return GenerateScheduleResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            total_entries=result.get("placed", 0),
            conflict_count=result.get("conflicts", 0),
        )

    @staticmethod
    def move_entry(
        db: Session, entry_id: int, data: TimetableMoveRequest
    ) -> TimetableEntryResponse:
        """
        移动课表条目（拖拽操作）

        流程：
        1. 查找条目
        2. 检查是否锁定
        3. 获取目标时间段的起止时间
        4. 检查冲突
        5. 执行移动
        """
        entry = db.query(TimetableEntry).filter(TimetableEntry.id == entry_id).first()
        if not entry:
            raise ValueError("课表条目不存在")

        if entry.is_locked:
            raise ValueError("该条目已锁定，无法移动")

        # 获取目标时间段的起止时间
        target_slot = db.query(TimeSlot).filter(
            TimeSlot.schedule_template_id == entry.schedule_template_id,
            TimeSlot.day_of_week == data.day_of_week,
            TimeSlot.period_number == data.period_number,
            TimeSlot.period_type == "上课",
        ).first()

        if not target_slot:
            raise ValueError("目标时间段不存在或不是上课时段")

        # 检查冲突
        conflicts = check_all_conflicts(
            db,
            teacher_id=entry.teacher_id,
            class_group_id=entry.class_group_id,
            classroom_id=data.classroom_id or entry.classroom_id,
            day_of_week=data.day_of_week,
            start_time=target_slot.start_time,
            end_time=target_slot.end_time,
            odd_even_type=entry.odd_even_type,
            schedule_plan_id=entry.schedule_plan_id,
            exclude_entry_id=entry.id,
        )

        has_conflict = any(len(v) > 0 for v in conflicts.values())
        if has_conflict:
            conflict_details = []
            for conflict_type, conflict_entries in conflicts.items():
                for ce in conflict_entries:
                    conflict_details.append({
                        "type": conflict_type,
                        "entry_id": ce.id,
                        "subject_name": ce.subject.name if ce.subject else "",
                        "teacher_name": ce.teacher.real_name if ce.teacher else "",
                        "class_name": ce.class_group.name if ce.class_group else "",
                    })
            raise ValueError(f"移动冲突: {conflict_details}")

        # 执行移动
        entry.day_of_week = data.day_of_week
        entry.period_number = data.period_number
        entry.start_time = target_slot.start_time
        entry.end_time = target_slot.end_time
        if data.classroom_id is not None:
            entry.classroom_id = data.classroom_id
        entry.updated_at = datetime.now()

        db.commit()
        db.refresh(entry)

        resp = TimetableEntryResponse.model_validate(entry)
        if entry.class_group:
            resp.class_name = entry.class_group.name
        if entry.subject:
            resp.subject_name = entry.subject.name
            resp.subject_short_name = entry.subject.short_name
        if entry.teacher:
            resp.teacher_name = entry.teacher.real_name
        if entry.classroom:
            resp.classroom_name = entry.classroom.name
        return resp

    @staticmethod
    def check_conflict(
        db: Session, data: ConflictCheckRequest
    ) -> ConflictCheckResponse:
        """
        检查移动是否会产生冲突（不实际移动）
        """
        entry = db.query(TimetableEntry).filter(TimetableEntry.id == data.entry_id).first()
        if not entry:
            raise ValueError("课表条目不存在")

        # 获取目标时间段的起止时间
        target_slot = db.query(TimeSlot).filter(
            TimeSlot.schedule_template_id == entry.schedule_template_id,
            TimeSlot.day_of_week == data.day_of_week,
            TimeSlot.period_number == data.period_number,
            TimeSlot.period_type == "上课",
        ).first()

        if not target_slot:
            return ConflictCheckResponse(has_conflict=True, conflicts=[{
                "type": "slot", "message": "目标时间段不存在"
            }])

        conflicts = check_all_conflicts(
            db,
            teacher_id=entry.teacher_id,
            class_group_id=entry.class_group_id,
            classroom_id=data.classroom_id or entry.classroom_id,
            day_of_week=data.day_of_week,
            start_time=target_slot.start_time,
            end_time=target_slot.end_time,
            odd_even_type=entry.odd_even_type,
            schedule_plan_id=entry.schedule_plan_id,
            exclude_entry_id=entry.id,
        )

        conflict_list = []
        for conflict_type, conflict_entries in conflicts.items():
            for ce in conflict_entries:
                conflict_list.append({
                    "type": conflict_type,
                    "entry_id": ce.id,
                    "subject_name": ce.subject.name if ce.subject else "",
                    "teacher_name": ce.teacher.real_name if ce.teacher else "",
                    "class_name": ce.class_group.name if ce.class_group else "",
                    "day_of_week": ce.day_of_week,
                    "period_number": ce.period_number,
                })

        return ConflictCheckResponse(
            has_conflict=len(conflict_list) > 0,
            conflicts=conflict_list,
        )


class SchedulePlanService:
    """排课方案管理服务"""

    @staticmethod
    def list_plans(
        db: Session, academic_year_id: Optional[int] = None
    ) -> List[SchedulePlanResponse]:
        """获取排课方案列表"""
        query = db.query(SchedulePlan)
        if academic_year_id:
            query = query.filter(SchedulePlan.academic_year_id == academic_year_id)

        plans = query.order_by(SchedulePlan.created_at.desc()).all()
        return [SchedulePlanResponse.model_validate(p) for p in plans]

    @staticmethod
    def create_plan(db: Session, data: SchedulePlanCreate) -> SchedulePlanResponse:
        """创建排课方案"""
        plan = SchedulePlan(**data.model_dump())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return SchedulePlanResponse.model_validate(plan)

    @staticmethod
    def publish_plan(db: Session, plan_id: int) -> SchedulePlanResponse:
        """
        发布排课方案

        发布后：
        1. 方案状态变为 published
        2. 其他同同学期的方案取消激活
        3. 该方案设为激活
        """
        plan = db.query(SchedulePlan).filter(SchedulePlan.id == plan_id).first()
        if not plan:
            raise ValueError("排课方案不存在")

        if plan.status == "published":
            raise ValueError("方案已发布")

        # 取消其他方案的激活状态
        other_plans = db.query(SchedulePlan).filter(
            SchedulePlan.academic_year_id == plan.academic_year_id,
            SchedulePlan.semester_id == plan.semester_id,
            SchedulePlan.id != plan.id,
        ).all()
        for p in other_plans:
            p.is_active = False

        # 发布当前方案
        plan.status = "published"
        plan.is_active = True
        plan.updated_at = datetime.now()

        db.commit()
        db.refresh(plan)
        return SchedulePlanResponse.model_validate(plan)
