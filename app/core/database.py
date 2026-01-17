"""
Supabase 数据库连接
"""

from typing import Optional, List, Dict, Any
from supabase import create_client, Client
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """数据库连接类 (单例模式)"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 Supabase 客户端"""
        if Database._initialized:
            return

        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL 和 SUPABASE_KEY 必须在 .env 文件中配置")

        # 创建 Supabase 客户端 (使用匿名 key)
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )

        # 创建管理员客户端 (使用 service_role key, 绕过 RLS)
        self.admin_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
        )

        Database._initialized = True
        logger.info("Supabase 客户端初始化成功")

    def get_client(self, use_admin: bool = False) -> Client:
        """
        获取 Supabase 客户端

        Args:
            use_admin: 是否使用管理员客户端 (绕过 RLS)

        Returns:
            Supabase 客户端实例
        """
        return self.admin_client if use_admin else self.client


# 全局数据库实例
db = Database()


# ========================================
# 数据库操作函数
# ========================================

async def create_bubble_note(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建新的气泡笔记

    Args:
        data: 笔记数据字典

    Returns:
        插入后的笔记数据 (包含生成的 id)
    """
    try:
        client = db.get_client(use_admin=True)

        # 插入数据
        response = client.table("bubble_note").insert({
            "user_id": data["user_id"],
            "note_type": data["note_type"],
            "content": data["content"],
            "image_urls": data.get("image_urls"),
            "gps_longitude": data["gps_longitude"],
            "gps_latitude": data["gps_latitude"],
            "status": data.get("status", 1),
            "emotion": data.get("emotion", "未知"),
        }).execute()

        if response.data:
            logger.info(f"成功创建气泡笔记, id={response.data[0]['id']}")
            return response.data[0]
        else:
            raise Exception("创建笔记失败: 无返回数据")

    except Exception as e:
        logger.error(f"创建气泡笔记失败: {e}")
        raise


async def update_bubble_note(note_id: int, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    更新气泡笔记

    Args:
        note_id: 笔记 ID
        user_id: 用户 ID (用于权限验证)
        data: 更新数据字典

    Returns:
        更新后的笔记数据, 如果不存在或无权限则返回 None
    """
    try:
        client = db.get_client(use_admin=True)

        # 先检查笔记是否存在且属于该用户
        check_response = client.table("bubble_note").select("*").eq("id", note_id).execute()

        if not check_response.data:
            logger.warning(f"笔记不存在, id={note_id}")
            return None

        existing_note = check_response.data[0]
        if existing_note["user_id"] != user_id:
            logger.warning(f"用户无权限修改该笔记, user_id={user_id}, note_id={note_id}")
            return None

        # 构建更新数据 (只更新允许修改的字段)
        update_data = {}
        if "note_type" in data:
            update_data["note_type"] = data["note_type"]
        if "content" in data:
            update_data["content"] = data["content"]
        if "image_urls" in data:
            update_data["image_urls"] = data["image_urls"]
        if "gps_longitude" in data:
            update_data["gps_longitude"] = data["gps_longitude"]
        if "gps_latitude" in data:
            update_data["gps_latitude"] = data["gps_latitude"]
        if "status" in data:
            update_data["status"] = data["status"]
        if "emotion" in data:
            update_data["emotion"] = data["emotion"]

        # 执行更新
        response = client.table("bubble_note").update(update_data).eq("id", note_id).execute()

        if response.data:
            logger.info(f"成功更新气泡笔记, id={note_id}")
            return response.data[0]
        else:
            return None

    except Exception as e:
        logger.error(f"更新气泡笔记失败: {e}")
        raise


async def get_bubble_note_by_id(note_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 ID 获取气泡笔记

    Args:
        note_id: 笔记 ID

    Returns:
        笔记数据, 如果不存在则返回 None
    """
    try:
        client = db.get_client()
        response = client.table("bubble_note").select("*").eq("id", note_id).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        logger.error(f"获取气泡笔记失败: {e}")
        raise


async def get_nearby_bubbles(
    longitude: float,
    latitude: float,
    radius_km: float = 1.0,
    limit: int = 20,
    status: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取附近的气泡笔记 (使用 PostGIS 地理查询)

    Args:
        longitude: 经度
        latitude: 纬度
        radius_km: 半径 (公里)
        limit: 返回数量限制
        status: 状态筛选 (1-公开/2-私有), None 表示全部

    Returns:
        附近的笔记列表
    """
    try:
        client = db.get_client()

        # 使用 PostGIS 的 ST_DWithin 函数查询附近的点
        # 注意: Supabase RPC 需要在数据库中预先定义函数
        # 这里使用原生 SQL 查询
        query = f"""
        SELECT *,
               ST_Distance(
                   location,
                   ST_SetSRID(ST_MakePoint($1, $2), 4326)::GEOGRAPHY
               ) as distance_meters
        FROM bubble_note
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint($1, $2), 4326)::GEOGRAPHY,
            $3
        )
        AND is_valid = 1
        {f"AND status = {status}" if status else ""}
        ORDER BY distance_meters ASC
        LIMIT $4
        """

        # 执行 SQL 查询 (需要使用 postgres_rpc)
        response = client.rpc(
            "get_nearby_bubbles",
            {
                "lon": longitude,
                "lat": latitude,
                "radius_m": int(radius_km * 1000),
                "lim": limit,
                "stat": status
            }
        ).execute()

        if response.data:
            return response.data
        return []

    except Exception as e:
        logger.error(f"获取附近气泡失败: {e}")
        # 如果 RPC 不可用,回退到普通查询 (不含距离)
        return await _get_nearby_bubbles_fallback(longitude, latitude, limit, status)


async def _get_nearby_bubbles_fallback(
    longitude: float,
    latitude: float,
    limit: int = 20,
    status: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取附近气泡的降级方案 (不使用 PostGIS, 简单的边界框查询)

    Args:
        longitude: 经度
        latitude: 纬度
        limit: 返回数量限制
        status: 状态筛选

    Returns:
        附近的笔记列表
    """
    try:
        client = db.get_client()

        # 计算边界框 (约1公里)
        delta_lon = 0.01  # 约1公里
        delta_lat = 0.01

        query = client.table("bubble_note").select("*")
        query = query.gte("gps_longitude", longitude - delta_lon)
        query = query.lte("gps_longitude", longitude + delta_lon)
        query = query.gte("gps_latitude", latitude - delta_lat)
        query = query.lte("gps_latitude", latitude + delta_lat)
        query = query.eq("is_valid", 1)

        if status is not None:
            query = query.eq("status", status)

        query = query.order("weight_score", desc=True).limit(limit)
        response = query.execute()

        if response.data:
            return response.data
        return []

    except Exception as e:
        logger.error(f"降级查询失败: {e}")
        return []


async def get_top_bubbles(limit: int = 20, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    获取权重最高的 Top N 气泡

    Args:
        limit: 返回数量限制
        user_id: 用户 ID (可选, 如果指定则只返回该用户的笔记)

    Returns:
        Top 笔记列表
    """
    try:
        client = db.get_client()

        query = client.table("bubble_note").select("*")
        query = query.eq("is_valid", 1)
        query = query.eq("status", 1)  # 只返回公开笔记

        if user_id is not None:
            query = query.eq("user_id", user_id)

        query = query.order("weight_score", desc=True).limit(limit)
        response = query.execute()

        if response.data:
            return response.data
        return []

    except Exception as e:
        logger.error(f"获取 Top 气泡失败: {e}")
        return []


async def delete_bubble_note(note_id: int, user_id: int) -> bool:
    """
    删除气泡笔记 (软删除, 设置 is_valid = 0)

    Args:
        note_id: 笔记 ID
        user_id: 用户 ID

    Returns:
        是否删除成功
    """
    try:
        client = db.get_client(use_admin=True)

        # 先检查权限
        check_response = client.table("bubble_note").select("*").eq("id", note_id).execute()

        if not check_response.data:
            return False

        existing_note = check_response.data[0]
        if existing_note["user_id"] != user_id:
            return False

        # 软删除
        response = client.table("bubble_note").update({"is_valid": 0}).eq("id", note_id).execute()

        if response.data:
            logger.info(f"成功删除气泡笔记, id={note_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"删除气泡笔记失败: {e}")
        return False


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    # 测试数据库连接
    print("测试 Supabase 连接...")

    try:
        # 测试查询
        result = db.client.table("bubble_note").select("*").limit(1).execute()
        print(f"连接成功! 查询结果: {result.data}")
    except Exception as e:
        print(f"连接失败: {e}")
