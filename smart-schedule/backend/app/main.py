"""
FastAPI 应用入口文件
- 创建应用实例
- 注册中间件
- 注册路由
- 启动事件处理
- WebSocket 端点
- 异常处理
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, SessionLocal
from app.utils.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库和默认管理员"""
    # 初始化数据库表结构
    init_db()

    # 创建默认管理员用户（如果不存在）
    _create_default_admin()

    yield

    # 应用关闭时清理资源
    for user_id in list(websocket_manager.active_connections.keys()):
        for ws in websocket_manager.active_connections[user_id]:
            try:
                await ws.close()
            except Exception:
                pass
    websocket_manager.active_connections.clear()


def _create_default_admin():
    """创建默认管理员账号"""
    from app.models.user import User
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                gender="男",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("默认管理员账号已创建: admin / admin123")
    except Exception as e:
        db.rollback()
        print(f"创建默认管理员失败: {e}")
    finally:
        db.close()


# ==================== WebSocket 连接管理器 ====================

class ConnectionManager:
    """WebSocket 连接管理器，用于实时通知推送"""

    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开 WebSocket 连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        """向指定用户推送消息"""
        if user_id in self.active_connections:
            dead_connections = set()
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_connections.add(ws)
            # 清理断开的连接
            for ws in dead_connections:
                self.active_connections[user_id].discard(ws)

    async def broadcast(self, message: dict):
        """向所有在线用户广播消息"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


websocket_manager = ConnectionManager()


# ==================== 创建 FastAPI 应用 ====================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能排课系统后端API",
    lifespan=lifespan,
)


# ==================== CORS 中间件 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== SPA 路由回退中间件 ====================

# 前端构建目录路径
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
FRONTEND_DIST = os.path.join(_BASE_DIR, "frontend", "dist")
FRONTEND_INDEX = os.path.join(FRONTEND_DIST, "index.html")

# 挂载静态资源（如果dist目录存在）
if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    for item in os.listdir(FRONTEND_DIST):
        item_path = os.path.join(FRONTEND_DIST, item)
        if os.path.isdir(item_path) and item != "assets":
            app.mount(f"/{item}", StaticFiles(directory=item_path), name=item)


@app.middleware("http")
async def spa_router_middleware(request: Request, call_next):
    """SPA 单页应用路由回退中间件"""
    path = request.url.path

    # API/文档/WebSocket/静态资源路径直接放行
    if (path.startswith("/api/") or path == "/api" or
            path.startswith("/docs") or path.startswith("/redoc") or
            path == "/openapi.json" or path.startswith("/openapi") or
            path.startswith("/ws/") or path.startswith("/assets/")):
        return await call_next(request)

    # 根路径交给后面的路由处理
    if path == "/":
        return await call_next(request)

    # 其他 GET 请求：尝试作为静态文件或返回 index.html
    if request.method == "GET":
        if not os.path.exists(FRONTEND_INDEX):
            return await call_next(request)
        possible_file = os.path.join(FRONTEND_DIST, path.lstrip("/"))
        if os.path.isfile(possible_file):
            return FileResponse(possible_file)
        return FileResponse(FRONTEND_INDEX)

    return await call_next(request)


# ==================== 注册路由 ====================

from app.api import (  # noqa: E402
    auth, users, academic, classes, subjects, classrooms,
    schedules, timetables, teaching, swap, notifications, staff, backup,
    export, logs,
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(academic.router, prefix="/api/academic-years", tags=["学年管理"])
app.include_router(classes.router, prefix="/api/classes", tags=["班级管理"])
app.include_router(subjects.router, prefix="/api/subjects", tags=["科目管理"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["教室管理"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["作息时间"])
app.include_router(timetables.router, prefix="/api/timetables", tags=["课表管理"])
app.include_router(teaching.router, prefix="/api/teaching", tags=["任课安排"])
app.include_router(swap.router, prefix="/api/swaps", tags=["调课管理"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知管理"])
app.include_router(staff.router, prefix="/api/staff", tags=["人事表"])
app.include_router(backup.router, prefix="/api/backups", tags=["备份管理"])
app.include_router(export.router, prefix="/api/export", tags=["导出导入"])
app.include_router(logs.router, prefix="/api/logs", tags=["操作日志"])


# ==================== WebSocket 端点 ====================

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """
    WebSocket 实时通知端点
    客户端连接后可接收服务端推送的通知消息
    """
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # 保持连接，接收客户端心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)


# ==================== 全局异常处理 ====================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """处理业务逻辑中的 ValueError"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    """处理权限错误"""
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """处理文件未找到错误"""
    return JSONResponse(
        status_code=404,
        content={"detail": "请求的资源不存在"},
    )


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_root():
    """根路径：返回前端 index.html 或欢迎页"""
    if os.path.exists(FRONTEND_INDEX):
        return FRONTEND_INDEX
    return FileResponse(
        path=os.path.join(os.path.dirname(__file__), "templates", "welcome.html"),
        media_type="text/html",
    )
