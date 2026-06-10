# 模型包 - 导入所有模型以便 SQLAlchemy 注册
from app.models.user import User
from app.models.academic import AcademicYear, Semester, Grade
from app.models.class_model import ClassGroup
from app.models.subject import Subject, SubjectSubMapping
from app.models.classroom import Classroom
from app.models.schedule import ScheduleTemplate, TimeSlot
from app.models.timetable import TeachingAssignment, PreScheduledCourse, SchedulePlan, TimetableEntry
from app.models.swap import CourseSwapRequest
from app.models.notification import Notification
from app.models.staff import StaffTableEntry
from app.models.backup import BackupRecord, OperationLog

__all__ = [
    "User",
    "AcademicYear", "Semester", "Grade",
    "ClassGroup",
    "Subject", "SubjectSubMapping",
    "Classroom",
    "ScheduleTemplate", "TimeSlot",
    "TeachingAssignment", "PreScheduledCourse", "SchedulePlan", "TimetableEntry",
    "CourseSwapRequest",
    "Notification",
    "StaffTableEntry",
    "BackupRecord", "OperationLog",
]
