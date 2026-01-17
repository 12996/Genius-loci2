"""API v1 路由"""

from fastapi import APIRouter
from app.api.v1 import bubbles

# 创建 v1 路由器
router = APIRouter(prefix="/v1")

# 注册各模块路由
router.include_router(bubbles.router, tags=["气泡笔记"])

__all__ = ["router"]
