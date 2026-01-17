"""
气泡笔记 API 路由
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import ValidationError

from app.models.schemas import (
    BubbleNoteCreate,
    BubbleNoteResponse,
    ApiResponse,
    BubbleNoteListResponse,
)
from app.services.bubble_service import bubble_service
from app.core.database import get_nearby_bubbles, get_top_bubbles
import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/bubbles", tags=["气泡笔记"])


# ========================================
# 核心 API: 创建/更新气泡笔记
# ========================================

@router.post(
    "/note",
    response_model=ApiResponse,
    summary="创建或更新气泡笔记 (纯文本)",
    description="使用 JSON 格式创建或更新气泡笔记,不含图片"
)
async def create_or_update_bubble_note_json(note_data: BubbleNoteCreate):
    """创建或更新气泡笔记 (JSON 格式, 不含图片)"""

    try:
        # 调用服务层处理
        result = await bubble_service.create_or_update_note(note_data)

        # 返回结果
        return ApiResponse(
            code=200,
            message=f"{'更新' if result['is_update'] else '创建'}成功",
            data={
                "note_id": result["note_id"],
                "emotion": result["emotion"],
                "note_type": result["note_type"]
            }
        )

    except ValidationError as e:
        logger.error(f"参数校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": "请求参数不合法",
                "detail": str(e)
            }
        )
    except ValueError as e:
        logger.error(f"业务校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": str(e),
                "detail": None
            }
        )
    except Exception as e:
        logger.error(f"服务处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


@router.post(
    "/note/with-image",
    response_model=ApiResponse,
    summary="创建或更新气泡笔记 (支持图片)",
    description="使用 multipart/form-data 创建或更新气泡笔记,图片可选"
)
async def create_or_update_bubble_note_with_image(
    user_id: int = Form(..., description="用户 ID"),
    content: Optional[str] = Form(None, description="笔记文本内容"),
    gps_longitude: float = Form(..., description="经度 [-180, 180]"),
    gps_latitude: float = Form(..., description="纬度 [-90, 90]"),
    note_status: int = Form(1, description="笔记状态 (1-公开/2-私有)"),
    note_id: Optional[int] = Form(None, description="笔记 ID (更新模式时必填)"),
    image: Optional[UploadFile] = File(None, description="图片文件 (可选)")
):
    """创建或更新气泡笔记 (支持 multipart/form-data)"""

    try:
        # 1. 读取图片数据 (单个)
        images_data = None
        if image:
            content_bytes = await image.read()
            images_data = [content_bytes]  # 转换为列表以兼容现有逻辑
            logger.info(f"接收到图片: {image.filename}, 大小: {len(content_bytes)} bytes")

        # 2. 构建请求数据模型
        note_data = BubbleNoteCreate(
            user_id=user_id,
            content=content,
            gps_longitude=gps_longitude,
            gps_latitude=gps_latitude,
            status=note_status,
            note_id=note_id
        )

        # 3. 调用服务层处理 (图片数据作为单独参数传递)
        result = await bubble_service.create_or_update_note(note_data, images_data)

        # 4. 返回结果
        return ApiResponse(
            code=200,
            message=f"{'更新' if result['is_update'] else '创建'}成功",
            data={
                "note_id": result["note_id"],
                "emotion": result["emotion"],
                "note_type": result["note_type"]
            }
        )

    except ValidationError as e:
        logger.error(f"参数校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": "请求参数不合法",
                "detail": str(e)
            }
        )
    except ValueError as e:
        logger.error(f"业务校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": str(e),
                "detail": None
            }
        )
    except Exception as e:
        logger.error(f"服务处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ========================================
# 查询 API: 获取附近气泡
# ========================================

@router.get(
    "/nearby",
    response_model=BubbleNoteListResponse,
    summary="获取附近的气泡笔记",
    description="""
    查询指定位置附近的气泡笔记 (使用 PostGIS 地理查询)

    **参数:**
    - longitude: 中心点经度
    - latitude: 中心点纬度
    - radius_km: 搜索半径 (公里), 默认 1.0
    - limit: 返回数量限制, 默认 20
    - status: 状态筛选 (1-公开/2-私有), 默认全部
    """
)
async def get_nearby_bubbles_api(
    longitude: float,
    latitude: float,
    radius_km: float = 1.0,
    limit: int = 20,
    status: Optional[int] = None
):
    """获取附近的气泡笔记"""

    try:
        # 参数校验
        if not -180 <= longitude <= 180:
            raise ValueError("经度必须在 [-180, 180] 范围内")
        if not -90 <= latitude <= 90:
            raise ValueError("纬度必须在 [-90, 90] 范围内")
        if radius_km <= 0 or radius_km > 100:
            raise ValueError("半径必须在 (0, 100] 公里范围内")
        if limit <= 0 or limit > 100:
            raise ValueError("返回数量必须在 (0, 100] 范围内")

        # 查询附近气泡
        bubbles = await get_nearby_bubbles(
            longitude=longitude,
            latitude=latitude,
            radius_km=radius_km,
            limit=limit,
            status=status
        )

        return BubbleNoteListResponse(
            code=200,
            message="查询成功",
            data=bubbles,
            total=len(bubbles)
        )

    except ValueError as e:
        logger.error(f"参数校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": str(e),
                "detail": None
            }
        )
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ========================================
# 查询 API: 获取 Top 气泡
# ========================================

@router.get(
    "/top",
    response_model=BubbleNoteListResponse,
    summary="获取权重最高的 Top N 气泡",
    description="""
    获取权重最高的气泡笔记

    **参数:**
    - limit: 返回数量限制, 默认 20
    - user_id: 用户 ID (可选), 如果指定则只返回该用户的笔记
    """
)
async def get_top_bubbles_api(
    limit: int = 20,
    user_id: Optional[int] = None
):
    """获取权重最高的 Top N 气泡"""

    try:
        if limit <= 0 or limit > 100:
            raise ValueError("返回数量必须在 (0, 100] 范围内")

        bubbles = await get_top_bubbles(limit=limit, user_id=user_id)

        return BubbleNoteListResponse(
            code=200,
            message="查询成功",
            data=bubbles,
            total=len(bubbles)
        )

    except ValueError as e:
        logger.error(f"参数校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": str(e),
                "detail": None
            }
        )
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ========================================
# 删除 API: 删除气泡笔记
# ========================================

@router.delete(
    "/note/{note_id}",
    response_model=ApiResponse,
    summary="删除气泡笔记",
    description="软删除气泡笔记 (设置 is_valid = 0)"
)
async def delete_bubble_note_api(note_id: int, user_id: int):
    """删除气泡笔记"""

    try:
        success = await bubble_service.delete_note(note_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": 404,
                    "message": "笔记不存在或无权限删除",
                    "detail": f"note_id={note_id}"
                }
            )

        return ApiResponse(
            code=200,
            message="删除成功",
            data={"note_id": note_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ========================================
# 健康检查
# ========================================

@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "bubble-note-api"
    }
