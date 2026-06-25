"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import engine, SessionLocal
from app.api import auth, users, posts, records, files, messages, dashboard, approvers, reports, configs, report_configs, audit_logs, role_modules, modules
from app.core.security import hash_password
from app.services.bootstrap import ensure_default_passwords, ensure_default_role_modules, ensure_builtin_modules
from app.services.scheduler import start_scheduler, stop_scheduler

# 日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭钩子"""
    # 启动
    logger.info("🚀 启动车辆管理系统...")
    # 健康检查 DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ 数据库连接成功")
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        raise

    # 重置默认密码 + 写入内置模块 + 默认角色模块权限（首次启动时）
    db = SessionLocal()
    try:
        ensure_default_passwords(db)
        ensure_builtin_modules(db)
        ensure_default_role_modules(db)
    finally:
        db.close()

    # 启动定时任务
    start_scheduler()

    yield

    # 关闭
    logger.info("🛑 关闭车辆管理系统...")
    stop_scheduler()
    engine.dispose()


app = FastAPI(
    title="厂区车辆进出管理系统 API",
    description="部署于群晖 NAS，多岗亭协作，拍照水印，多级审批",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    # 关闭自动 trailing slash 重定向，避免 CORS 跨域问题
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 统一响应格式
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数错误",
            "data": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理异常: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )


# 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["岗亭管理"])
app.include_router(records.router, prefix="/api/v1/records", tags=["进出记录"])
app.include_router(files.router, prefix="/api/v1/files", tags=["文件上传"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["站内消息"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["仪表盘"])
app.include_router(approvers.router, prefix="/api/v1/approvers", tags=["审批人"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["报表"])
app.include_router(configs.router, prefix="/api/v1/system", tags=["系统配置"])
app.include_router(report_configs.router, prefix="/api/v1/report-configs", tags=["推送配置"])
app.include_router(audit_logs.router, prefix="/api/v1/audit-logs", tags=["审计日志"])
app.include_router(role_modules.router, prefix="/api/v1/role-modules", tags=["角色权限"])
app.include_router(modules.router, prefix="/api/v1/modules", tags=["自定义模块"])


# 照片静态目录（upload_photo 返回的 /photos/{rel_path} 在这里 serve）
import os as _os
_PHOTOS_DIR = _os.environ.get("PHOTO_BASE_DIR", "/photos")
if _os.path.isdir(_PHOTOS_DIR):
    app.mount("/photos", StaticFiles(directory=_PHOTOS_DIR), name="photos")

@app.get("/")
async def root():
    return {
        "code": 0,
        "message": "厂区车辆进出管理系统 API",
        "data": {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """健康检查"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"code": 503, "message": f"unhealthy: {e}", "data": None},
        )
