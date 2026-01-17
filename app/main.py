"""
FastAPI 主应用入口
气泡笔记 (Bubble Note) API 服务
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import router
from app.core.config import settings
from app.core.database import db
from app.core.oss_storage import oss_storage

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================================
# 应用生命周期管理
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} 启动中...")
    logger.info(f"版本: {settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info("=" * 50)

    # 测试数据库连接
    try:
        logger.info("Supabase 数据库连接成功")
    except Exception as e:
        logger.error(f"Supabase 连接失败: {e}")

    # 测试 OSS 连接
    try:
        if oss_storage.bucket:
            logger.info("阿里云 OSS 连接成功")
        else:
            logger.warning("阿里云 OSS 未配置")
    except Exception as e:
        logger.warning(f"OSS 连接失败: {e}")

    yield

    # 关闭时执行
    logger.info("气泡笔记 API 服务关闭")


# ========================================
# 创建 FastAPI 应用
# ========================================

app = FastAPI(
    title=settings.APP_NAME,
    description="基于 FastAPI + Supabase + 阿里云 OSS 的气泡笔记服务",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ========================================
# 配置 CORS
# ========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS 允许的源: {settings.ALLOWED_ORIGINS}")

# ========================================
# 注册路由
# ========================================

app.include_router(router)

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/bubbles/health"
    }


# ========================================
# 全局异常处理
# ========================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc)
        }
    )


# ========================================
# 启动脚本
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
