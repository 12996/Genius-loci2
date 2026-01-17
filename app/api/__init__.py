"""API 路由"""

from fastapi import APIRouter
from app.api.v1 import router as v1_router

# 创建 API 路由器
router = APIRouter(prefix="/api")

# 注册 v1 路由
router.include_router(v1_router)

__all__ = ["router"]
