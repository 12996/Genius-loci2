"""配置管理"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置"""

    # 应用信息
    APP_NAME: str = os.getenv("APP_NAME", "气泡笔记 API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS 配置
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # Supabase 配置
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # 阿里云 OSS 配置
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    OSS_BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME", "")
    OSS_BUCKET_DOMAIN: str = os.getenv("OSS_BUCKET_DOMAIN", "")

    # 魔搭模型配置（对话模型）
    MODEL_NAME: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
    MODEL_API_KEY: str = os.getenv("MODEL_API_KEY", "")
    MODEL_API_URL: str = os.getenv(
        "MODEL_API_URL",
        "https://api-inference.modelscope.cn/v1/chat/completions"
    )
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TOP_P: float = float(os.getenv("TOP_P", "0.9"))

    # 视觉模型配置
    VISION_MODEL_NAME: str = os.getenv("VISION_MODEL_NAME", "gpt-4o")
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_API_URL: str = os.getenv(
        "VISION_API_URL",
        "https://api.openai.com/v1/chat/completions"
    )

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
