"""
数据库连接和会话管理模块
使用 SQLAlchemy 2.0 风格，支持异步和同步两种模式
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

from app.config import settings


# 创建数据库引擎 (MySQL 5.7 兼容)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_recycle=3600,   # 连接回收时间（秒）
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    # MySQL 5.7 兼容性设置
    connect_args={
        "charset": "utf8mb4",
    },
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型继承此类"""
    pass


def get_db() -> Generator:
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 的 Depends 注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册
    from app.models import (  # noqa: F401
        user, academic, class_model, subject, classroom,
        schedule, timetable, swap, notification, staff, backup,
    )
    Base.metadata.create_all(bind=engine)
