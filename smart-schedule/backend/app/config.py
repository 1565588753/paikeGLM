"""
应用配置模块 - 使用 pydantic-settings 管理所有配置项
支持从环境变量和 .env 文件读取配置
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional


# 项目根目录（backend/目录）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置类，所有配置项均可通过环境变量覆盖"""

    # 数据库连接配置 (MySQL 5.7)
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/smart_schedule"

    # Redis 连接配置 (用于缓存和实时通知)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 密钥和过期时间
    SECRET_KEY: str = "smart-schedule-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小时

    # 备份配置
    BACKUP_DIR: str = str(BASE_DIR / "backups")
    BACKUP_CRON: str = "0 2 * * *"  # 每天凌晨2点自动备份

    # 日志目录
    LOG_DIR: str = str(BASE_DIR / "logs")

    # CORS 跨域配置（生产环境应替换为实际域名）
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1",
        "http://localhost",
    ]

    # 应用信息
    APP_NAME: str = "智能排课系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 运行环境
    ENVIRONMENT: str = "development"

    # 服务端口
    PORT: int = 8000

    # 分页默认值
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    model_config = {
        # .env 文件路径：优先从当前工作目录读取，兼容宝塔部署
        "env_file": [".env", str(BASE_DIR / ".env")],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # 忽略 .env 中多余的变量
    }


# 全局配置实例
settings = Settings()
