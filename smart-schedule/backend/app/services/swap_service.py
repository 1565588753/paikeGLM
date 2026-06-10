"""
调课服务模块
- 调课请求的创建、审批、拒绝
- 完整的调课工作流
- 冲突检查
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.swap import CourseSwapRequest
from app.models.timetable import TimetableEntry
from app.models.notification import Notification
from app.engine.conflict import check_all_conflicts, has_any_conflict
from app.schemas.swap import CourseSwapCreate, CourseSwapRespond, CourseSwapResponse


class SwapService:
    """调课管理服务"""

    @staticmethod
    def list_swap_requests(
        db: Session,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取调课请求列表"""
        query = db.query(CourseSwapRequest)

        if user_id:
            query = query.filter(
                (CourseSwapRequest.requester_id == user_id) |
                (CourseSwapRequest.target_id == user_id)
            )
        if status:
            query = query.filter(CourseSwapRequest.status == status)

        total = query.count()
        requests = query.order_by(CourseSwapRequest.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = []
        for r in requests:
            resp = CourseSwapResponse.model_validate(r)
            if r.requester:
                resp.requester_name = r.requester.real_name
            if r.target:
                resp.target_name = r.target.real_name
            items.append(resp)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create_swap_request(
        db: Session, requester_id: int, data: CourseSwapCreate
    ) -> CourseSwapResponse:
        """
        创建调课请求

        流程：
        1. 验证请求者和目标条目
        2. 确认请求者是其中一个条目的教师
        3. 创建调课请求
        4. 发送通知给目标教师
        """
        # 获取请求者的课表条目
        requester_entry = db.query(TimetableEntry).filter(
            TimetableEntry.id == data.requester_entry_id
        ).first()
        if not requester_entry:
            raise ValueError("请求者的课表条目不存在")

        # 验证请求者是该条目的教师
        if requester_entry.teacher_id != requester_id:
            raise ValueError("您不是该课表条目的任课教师")

        # 获取目标课表条目
        target_entry = db.query(TimetableEntry).filter(
            TimetableEntry.id == data.target_entry_id
        ).first()
        if not target_entry:
            raise ValueError("目标课表条目不存在")

        # 不能和自己调课
        if requester_entry.teacher_id == target_entry.teacher_id:
            raise ValueError("不能和自己调课")

        # 检查是否已有待处理的调课请求
        existing = db.query(CourseSwapRequest).filter(
            CourseSwapRequest.requester_entry_id == data.requester_entry_id,
            CourseSwapRequest.target_entry_id == data.target_entry_id,
            CourseSwapRequest.status == "pending",
        ).first()
        if existing:
            raise ValueError("已存在待处理的调课请求")

        # 创建调课请求
        swap_request = CourseSwapRequest(
            requester_id=requester_id,
            target_id=target_entry.teacher_id,
            requester_entry_id=data.requester_entry_id,
            target_entry_id=data.target_entry_id,
            reason=data.reason,
            status="pending",
            academic_year_id=requester_entry.schedule_plan.academic_year_id if requester_entry.schedule_plan else 0,
        )
        db.add(swap_request)

        # 发送通知给目标教师
        notification = Notification(
            user_id=target_entry.teacher_id,
            type="swap_request",
            title="收到调课请求",
            content=f"{requester_entry.teacher.real_name if requester_entry.teacher else ''} 请求与您调课，原因：{data.reason or '无'}",
            related_id=swap_request.id,
        )
        db.add(notification)

        db.commit()
        db.refresh(swap_request)

        resp = CourseSwapResponse.model_validate(swap_request)
        if swap_request.requester:
            resp.requester_name = swap_request.requester.real_name
        if swap_request.target:
            resp.target_name = swap_request.target.real_name
        return resp

    @staticmethod
    def respond_swap_request(
        db: Session, swap_id: int, responder_id: int, data: CourseSwapRespond
    ) -> CourseSwapResponse:
        """
        响应调课请求

        完整的调课工作流：
        1. 验证调课请求和响应者身份
        2. 如果同意，检查交换后是否会产生冲突
        3. 如果无冲突，执行交换（交换两个条目的时间和教室）
        4. 更新调课请求状态
        5. 发送通知给请求者
        """
        swap_request = db.query(CourseSwapRequest).filter(
            CourseSwapRequest.id == swap_id
        ).first()
        if not swap_request:
            raise ValueError("调课请求不存在")

        # 验证响应者是目标教师
        if swap_request.target_id != responder_id:
            raise ValueError("您无权处理此调课请求")

        # 验证请求状态
        if swap_request.status != "pending":
            raise ValueError("该调课请求已处理")

        # 获取两个课表条目
        requester_entry = db.query(TimetableEntry).filter(
            TimetableEntry.id == swap_request.requester_entry_id
        ).first()
        target_entry = db.query(TimetableEntry).filter(
            TimetableEntry.id == swap_request.target_entry_id
        ).first()

        if not requester_entry or not target_entry:
            raise ValueError("课表条目不存在")

        if data.approved:
            # ===== 同意调课 =====

            # 检查交换后的冲突
            # 请求者的课移到目标位置
            requester_conflicts = check_all_conflicts(
                db,
                teacher_id=requester_entry.teacher_id,
                class_group_id=requester_entry.class_group_id,
                classroom_id=target_entry.classroom_id,
                day_of_week=target_entry.day_of_week,
                start_time=target_entry.start_time,
                end_time=target_entry.end_time,
                odd_even_type=requester_entry.odd_even_type,
                schedule_plan_id=requester_entry.schedule_plan_id,
                exclude_entry_id=requester_entry.id,
            )

            # 目标教师的课移到请求者位置
            target_conflicts = check_all_conflicts(
                db,
                teacher_id=target_entry.teacher_id,
                class_group_id=target_entry.class_group_id,
                classroom_id=requester_entry.classroom_id,
                day_of_week=requester_entry.day_of_week,
                start_time=requester_entry.start_time,
                end_time=requester_entry.end_time,
                odd_even_type=target_entry.odd_even_type,
                schedule_plan_id=target_entry.schedule_plan_id,
                exclude_entry_id=target_entry.id,
            )

            # 检查是否有冲突（排除彼此之间的冲突）
            has_requester_conflict = any(
                len(v) > 0 for k, v in requester_conflicts.items() if k != "class"
            )
            has_target_conflict = any(
                len(v) > 0 for k, v in target_conflicts.items() if k != "class"
            )

            if has_requester_conflict or has_target_conflict:
                # 有冲突，拒绝调课
                swap_request.status = "rejected"
                swap_request.responder_reason = "调课后会产生时间冲突，无法调课"
                swap_request.resolved_at = datetime.now()

                notification = Notification(
                    user_id=swap_request.requester_id,
                    type="swap_result",
                    title="调课请求被拒绝",
                    content=f"您的调课请求因时间冲突被拒绝",
                    related_id=swap_request.id,
                )
                db.add(notification)
                db.commit()

                resp = CourseSwapResponse.model_validate(swap_request)
                return resp

            # 执行交换：交换两个条目的时间信息
            # 保存原始值
            r_day = requester_entry.day_of_week
            r_period = requester_entry.period_number
            r_start = requester_entry.start_time
            r_end = requester_entry.end_time
            r_template = requester_entry.schedule_template_id
            r_classroom = requester_entry.classroom_id

            t_day = target_entry.day_of_week
            t_period = target_entry.period_number
            t_start = target_entry.start_time
            t_end = target_entry.end_time
            t_template = target_entry.schedule_template_id
            t_classroom = target_entry.classroom_id

            # 交换
            requester_entry.day_of_week = t_day
            requester_entry.period_number = t_period
            requester_entry.start_time = t_start
            requester_entry.end_time = t_end
            requester_entry.schedule_template_id = t_template
            requester_entry.classroom_id = t_classroom
            requester_entry.updated_at = datetime.now()

            target_entry.day_of_week = r_day
            target_entry.period_number = r_period
            target_entry.start_time = r_start
            target_entry.end_time = r_end
            target_entry.schedule_template_id = r_template
            target_entry.classroom_id = r_classroom
            target_entry.updated_at = datetime.now()

            # 更新调课请求状态
            swap_request.status = "approved"
            swap_request.responder_reason = data.reason
            swap_request.resolved_at = datetime.now()

            # 通知请求者
            notification = Notification(
                user_id=swap_request.requester_id,
                type="swap_result",
                title="调课请求已同意",
                content=f"您的调课请求已被同意",
                related_id=swap_request.id,
            )
            db.add(notification)

        else:
            # ===== 拒绝调课 =====
            swap_request.status = "rejected"
            swap_request.responder_reason = data.reason
            swap_request.resolved_at = datetime.now()

            notification = Notification(
                user_id=swap_request.requester_id,
                type="swap_result",
                title="调课请求被拒绝",
                content=f"您的调课请求被拒绝，原因：{data.reason or '无'}",
                related_id=swap_request.id,
            )
            db.add(notification)

        db.commit()
        db.refresh(swap_request)

        resp = CourseSwapResponse.model_validate(swap_request)
        if swap_request.requester:
            resp.requester_name = swap_request.requester.real_name
        if swap_request.target:
            resp.target_name = swap_request.target.real_name
        return resp

    @staticmethod
    def cancel_swap_request(db: Session, swap_id: int, requester_id: int) -> bool:
        """取消调课请求"""
        swap_request = db.query(CourseSwapRequest).filter(
            CourseSwapRequest.id == swap_id
        ).first()
        if not swap_request:
            raise ValueError("调课请求不存在")

        if swap_request.requester_id != requester_id:
            raise ValueError("只能取消自己发起的调课请求")

        if swap_request.status != "pending":
            raise ValueError("只能取消待处理的调课请求")

        swap_request.status = "cancelled"
        swap_request.resolved_at = datetime.now()
        db.commit()
        return True
