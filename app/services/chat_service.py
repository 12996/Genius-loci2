"""
地灵对话流式响应服务
功能：调用对话大模型 API，实现流式对话和记忆总结
作者：Claude Sonnet 4.5
创建时间：2025-01-17
"""

import logging
import json
import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


# ========================================
# 地灵人设 System Prompt
# ========================================

GENIUS_LOCI_SYSTEM_PROMPT = """你是"地灵"（Genius Loci），一位温柔、博学、守护此地的灵体。

你的身份特征：
- 你是这片土地的守护者，见证了无数时光流转
- 你温柔亲切，像一位睿智的老朋友
- 你博学多才，了解此地的人文历史和风土人情
- 你说话时带有诗意和哲思，但不过于晦涩

你的对话风格：
1. 开场白：首次对话时，结合场景环境，用温暖的方式打招呼，营造归属感
2. 倾听与回应：认真倾听用户的心声，给予理解和共情
3. 建议与引导：适度提供建议，但不强加于人
4. 语言特点：温柔、诗意、有画面感，避免说教

重要约束：
- 不要提及你是一个AI或助手
- 保持角色的连贯性和真实感
- 回应长度控制在100-200字之间（除非用户特别需要详细回答）
"""


class ChatService:
    """对话服务类（单例模式）"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化对话服务"""
        if ChatService._initialized:
            return

        # 从配置读取对话模型设置
        self.api_key = settings.MODEL_API_KEY
        self.api_url = settings.MODEL_API_URL
        self.model_name = settings.MODEL_NAME
        self.temperature = settings.TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS
        self.top_p = settings.TOP_P

        if not self.api_key:
            logger.warning("对话模型 API Key 未配置")

        ChatService._initialized = True
        logger.info("对话服务初始化成功")

    async def chat_stream(
        self,
        user_message: str,
        session_history: List[Dict[str, str]] = None,
        system_context: str = None
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            user_message: 用户消息
            session_history: 会话历史列表（格式：[{"role": "user/assistant", "content": "..."}]）
            system_context: 系统上下文（场景描述 + 历史记忆）

        Yields:
            流式文本片段
        """
        try:
            if not self.api_key:
                raise ValueError("对话模型 API Key 未配置")

            # 构建消息列表
            messages = []

            # 1. 添加 System Prompt
            system_prompt = GENIUS_LOCI_SYSTEM_PROMPT
            if system_context:
                system_prompt += f"\n\n【当前场景与记忆】\n{system_context}"

            messages.append({
                "role": "system",
                "content": system_prompt
            })

            # 2. 添加历史对话
            if session_history:
                messages.extend(session_history[-10:])  # 只保留最近10轮对话

            # 3. 添加当前用户消息
            messages.append({
                "role": "user",
                "content": user_message
            })

            # 构建请求体
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "stream": True  # 开启流式响应
            }

            # 发送流式请求
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"对话 API 调用失败: {response.status_code} - {error_text}")
                        raise Exception(f"API 调用失败: {response.status_code}")

                    # 逐行解析 SSE 流
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # SSE 格式: "data: {...}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 "data: " 前缀

                            # 检查是否为结束标志
                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)

                                # 提取文本内容
                                if data.get("choices"):
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")

                                    if content:
                                        logger.debug(f"流式输出: {content}")
                                        yield content

                            except json.JSONDecodeError:
                                logger.warning(f"无法解析 SSE 数据: {data_str}")
                                continue

        except Exception as e:
            logger.error(f"流式对话异常: {e}")
            raise

    async def summarize_conversation(
        self,
        conversation: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        总结对话内容（用于持久化存储）

        Args:
            conversation: 对话记录列表
                格式：[
                    {"role": "user", "content": "用户的问题"},
                    {"role": "assistant", "content": "地灵的回答"},
                    ...
                ]

        Returns:
            对话摘要文本（包含事情经过和情感变化），失败则返回 None
        """
        try:
            if not self.api_key:
                logger.warning("对话模型 API Key 未配置，无法总结对话")
                return None

            # 构建总结提示词
            summarize_prompt = """请将以下对话总结为一段简洁的文字，要求：
1. 保留事情的主要经过（用户说了什么、地灵如何回应）
2. 捕捉情感变化（用户的情绪、对话的氛围）
3. 突出关键信息和转折点
4. 字数控制在50-100字
5. 使用第三人称叙述

对话内容：
"""

            # 添加对话内容
            for msg in conversation:
                role = "用户" if msg["role"] == "user" else "地灵"
                summarize_prompt += f"\n{role}：{msg['content']}"

            # 构建请求
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的对话记录员，擅长总结对话内容并捕捉情感变化。"
                },
                {
                    "role": "user",
                    "content": summarize_prompt
                }
            ]

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.3,  # 降低温度，使总结更稳定
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
                    summary = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"对话总结成功: {summary}")
                    return summary
                else:
                    logger.error(f"总结 API 调用失败: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"对话总结异常: {e}")
            return None


# 全局对话服务实例
chat_service = ChatService()
