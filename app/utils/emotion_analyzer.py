"""
情感分析工具 - 集成魔搭模型
实现完整的情感识别逻辑流程

五种情感: 难过、开心、平静、神秘、愤怒
"""

import requests
from typing import Optional, List
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class EmotionConfig:
    """情感配置类"""
    # 五个预定义的情感词
    emotions: List[str] = None
    # 默认兜底情感
    default_emotion: str = "平静"

    def __post_init__(self):
        if self.emotions is None:
            self.emotions = ["难过", "开心", "平静", "神秘", "愤怒"]


class EmotionAnalyzer:
    """情感分析器核心类（单例模式）"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化情感分析器(单例, 只初始化一次)"""
        if EmotionAnalyzer._initialized:
            return

        self.config = EmotionConfig()
        self.api_key = settings.MODEL_API_KEY
        self.api_url = settings.MODEL_API_URL
        self.model_name = settings.MODEL_NAME

        self._setup_semantic_mapping()
        EmotionAnalyzer._initialized = True

    def _setup_semantic_mapping(self):
        """设置语义映射表，将相近词汇映射到预定义情感"""
        self.semantic_map = {
            "难过": ["悲伤", "伤心", "痛苦", "忧伤", "哀伤", "悲痛", "沮丧", "失落", "郁闷"],
            "开心": ["快乐", "高兴", "愉快", "欢乐", "喜悦", "幸福", "兴奋", "满足"],
            "平静": ["冷静", "安静", "淡定", "沉稳", "平和", "宁静", "从容"],
            "神秘": ["好奇", "疑惑", "探索", "未知", "玄妙", "深奥", "不可思议"],
            "愤怒": ["生气", "发怒", "暴怒", "恼火", "气愤", "激怒", "愤慨", "不爽"]
        }

    def _create_prompt(self, user_text: str) -> str:
        """
        创建发送给模型的Prompt

        Args:
            user_text: 用户输入的文本

        Returns:
            完整的Prompt字符串
        """
        prompt = f"""你是一位情感分析专家。请分析以下文本所表达的情感，并仅返回以下五个词之一：

- 难过
- 开心
- 平静
- 神秘
- 愤怒

待分析文本：{user_text}

请仅返回上述五个词之一，不要返回任何其他内容。"""
        return prompt

    def _query_model(self, user_text: str) -> str:
        """
        调用魔搭API进行情感分析

        Args:
            user_text: 待分析的文本

        Returns:
            模型输出的原始结果
        """
        try:
            prompt = self._create_prompt(user_text)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": settings.TEMPERATURE,
                "max_tokens": settings.MAX_TOKENS,
                "top_p": settings.TOP_P
            }

            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"API调用出错: {e}")
            return self.config.default_emotion

    def analyze(self, user_text: str) -> str:
        """
        分析用户文本的情感（完整流程）

        流程：
        1. 输入阶段：接收用户文本
        2. Prompt约束阶段：发送给模型并获取输出
        3. 解析对齐阶段：处理模型输出
           - 完全匹配
           - 关键词搜索
           - 语义映射
           - 兜底默认值

        Args:
            user_text: 用户输入的文本

        Returns:
            规范化后的情感词
        """
        # 输入阶段：接收用户文本
        # Prompt约束阶段：发送给模型并获取输出
        model_output = self._query_model(user_text)

        # 解析对齐阶段（核心）：处理模型输出
        return self._parse_model_output(model_output)

    def _parse_model_output(self, model_output: str) -> str:
        """
        解析对齐阶段（核心逻辑）

        Args:
            model_output: 模型返回的原始输出

        Returns:
            规范化后的情感词
        """
        # 步骤1: 完全匹配
        exact_match = self._exact_match(model_output)
        if exact_match:
            return exact_match

        # 步骤2: 关键词搜索
        keyword_match = self._keyword_search(model_output)
        if keyword_match:
            return keyword_match

        # 步骤3: 语义映射
        semantic_match = self._semantic_mapping(model_output)
        if semantic_match:
            return semantic_match

        # 步骤4: 兜底返回默认值
        return self.config.default_emotion

    def _exact_match(self, text: str) -> Optional[str]:
        """
        完全匹配检查
        直接检查输出是否为五个预定义词之一
        """
        cleaned_text = text.strip()
        if cleaned_text in self.config.emotions:
            return cleaned_text
        return None

    def _keyword_search(self, text: str) -> Optional[str]:
        """
        关键词搜索
        检查文本中是否包含预定义的情感关键词
        """
        for emotion in self.config.emotions:
            if emotion in text:
                return emotion
        return None

    def _semantic_mapping(self, text: str) -> Optional[str]:
        """
        语义映射
        将意思相近的词映射到预定义情感
        """
        for standard_emotion, similar_words in self.semantic_map.items():
            for word in similar_words:
                if word in text:
                    return standard_emotion
        return None



# 全局分析器实例
_analyzer = None


def analyze_emotion(text: str) -> str:
    """
    分析文本的情感（主入口函数）

    Args:
        text: 待分析的文本

    Returns:
        情感词（难过/开心/平静/神秘/愤怒）
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = EmotionAnalyzer()
    return _analyzer.analyze(text)


# 使用示例
if __name__ == "__main__":
    # 测试单个文本分析
    test_text = "我今天真的很开心，太棒了！"
    emotion = analyze_emotion(test_text)
    print(f"文本: {test_text}")
    print(f"情感: {emotion}")
