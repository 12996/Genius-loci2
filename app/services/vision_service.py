"""
多模态视觉感知服务
功能：调用视觉大模型 API，解析图片为场景文本描述
作者：Claude Sonnet 4.5
创建时间：2025-01-17
"""

import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class VisionService:
    """视觉感知服务类（单例模式）"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化视觉服务"""
        if VisionService._initialized:
            return

        # 从配置读取视觉模型设置
        self.api_key = getattr(settings, 'VISION_API_KEY', '')
        self.api_url = getattr(settings, 'VISION_API_URL', 'https://api.openai.com/v1/chat/completions')
        self.model_name = getattr(settings, 'VISION_MODEL_NAME', 'gpt-4o')

        if not self.api_key:
            logger.warning("视觉模型 API Key 未配置，视觉分析功能将不可用")

        VisionService._initialized = True
        logger.info("视觉感知服务初始化成功")

    async def analyze_image(self, image_url: str) -> Optional[str]:
        """
        分析图片，生成场景文本描述

        Args:
            image_url: 图片的 URL 地址（可以是 OSS URL 或其他网络地址）

        Returns:
            场景文本描述，失败则返回 None
        """
        try:
            if not self.api_key:
                logger.warning("视觉模型 API Key 未配置，跳过图片分析")
                return None

            # 构建请求体
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """请详细描述这张图片中的场景，包括：
1. 环境类型（如：咖啡厅、公园、办公室、街道等）
2. 光线情况（如：午后阳光充足、昏暗、明亮等）
3. 主要氛围特征（如：现代感、温馨、热闹、安静等）
4. 关键细节（如：装饰风格、人数、特殊元素等）

请用简洁但准确的语言描述，不超过100字。"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    description = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"视觉分析成功: {description}")
                    return description
                else:
                    logger.error(f"视觉 API 调用失败: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"视觉分析异常: {e}")
            return None


# 全局视觉服务实例
vision_service = VisionService()
