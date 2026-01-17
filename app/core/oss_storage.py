"""
阿里云 OSS 文件存储
"""

import asyncio
from typing import List, Optional
from datetime import datetime
import oss2
from oss2.exceptions import OssError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSSStorage:
    """阿里云 OSS 存储类 (单例模式)"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 OSS 客户端"""
        if OSSStorage._initialized:
            return

        if not all([settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET, settings.OSS_BUCKET_NAME]):
            logger.warning("OSS 配置不完整,图片上传功能将不可用")
            self.auth = None
            self.bucket = None
        else:
            # 创建认证对象
            self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            # 创建 Bucket 对象
            self.bucket = oss2.Bucket(self.auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            logger.info(f"OSS 客户端初始化成功: {settings.OSS_BUCKET_NAME}")

        OSSStorage._initialized = True

    def _generate_object_key(self, user_id: int, file_extension: str = "jpg") -> str:
        """
        生成 OSS 对象键 (文件路径)

        路径格式: bubbles/{YYYY}/{MM}/{DD}/{user_id}_{uuid}.jpg

        Args:
            user_id: 用户 ID
            file_extension: 文件扩展名

        Returns:
            OSS 对象键
        """
        now = datetime.utcnow()
        uuid_str = os.urandom(8).hex()
        return f"bubbles/{now.year}/{now.month:02d}/{now.day:02d}/{user_id}_{uuid_str}.{file_extension}"

    async def upload_single_image(
        self,
        image_data: bytes,
        user_id: int,
        file_extension: str = "jpg"
    ) -> Optional[str]:
        """
        上传单张图片到 OSS

        Args:
            image_data: 图片二进制数据
            user_id: 用户 ID
            file_extension: 文件扩展名

        Returns:
            图片 URL, 上传失败则返回 None
        """
        if not self.bucket:
            logger.error("OSS 客户端未初始化")
            return None

        try:
            # 生成对象键
            object_key = self._generate_object_key(user_id, file_extension)

            # 在线程池中执行上传 (避免阻塞事件循环)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.bucket.put_object(object_key, image_data)
            )

            # 构建图片 URL
            if settings.OSS_BUCKET_DOMAIN:
                image_url = f"{settings.OSS_BUCKET_DOMAIN}/{object_key}"
            else:
                image_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{object_key}"

            logger.info(f"图片上传成功: {object_key}")
            return image_url

        except OssError as e:
            logger.error(f"OSS 上传失败: {e}")
            return None
        except Exception as e:
            logger.error(f"上传图片时发生错误: {e}")
            return None

    async def upload_images_batch(
        self,
        images_data: List[bytes],
        user_id: int
    ) -> List[str]:
        """
        批量并发上传多张图片到 OSS

        Args:
            images_data: 图片二进制数据列表
            user_id: 用户 ID

        Returns:
            图片 URL 列表

        Raises:
            Exception: 如果任一图片上传失败,则抛出异常 (原子性保证)
        """
        if not images_data:
            return []

        if not self.bucket:
            raise Exception("OSS 客户端未初始化")

        try:
            # 并发上传所有图片
            upload_tasks = [
                self.upload_single_image(img_data, user_id)
                for img_data in images_data
            ]

            # 等待所有上传完成
            uploaded_urls = await asyncio.gather(*upload_tasks)

            # 检查是否有上传失败的
            if None in uploaded_urls:
                raise Exception("部分图片上传失败,终止流程")

            # 返回成功的 URL 列表
            result_urls = [url for url in uploaded_urls if url is not None]
            logger.info(f"批量上传成功: {len(result_urls)}/{len(images_data)} 张图片")
            return result_urls

        except Exception as e:
            logger.error(f"批量上传失败: {e}")
            raise

    async def delete_image(self, image_url: str) -> bool:
        """
        删除 OSS 中的图片

        Args:
            image_url: 图片 URL

        Returns:
            是否删除成功
        """
        if not self.bucket:
            return False

        try:
            # 从 URL 中提取对象键
            # URL 格式: https://bucket.endpoint/key
            if "/" in image_url:
                object_key = "/".join(image_url.split("/")[-4:])  # 提取 bubbles/... 部分
            else:
                return False

            # 删除对象
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.bucket.delete_object(object_key)
            )

            logger.info(f"图片删除成功: {object_key}")
            return True

        except OssError as e:
            logger.error(f"OSS 删除失败: {e}")
            return False
        except Exception as e:
            logger.error(f"删除图片时发生错误: {e}")
            return False


# 全局 OSS 实例
oss_storage = OSSStorage()


# ========================================
# 辅助函数
# ========================================

async def upload_images_from_files(
    file_paths: List[str],
    user_id: int
) -> List[str]:
    """
    从文件路径上传图片

    Args:
        file_paths: 图片文件路径列表
        user_id: 用户 ID

    Returns:
        图片 URL 列表
    """
    images_data = []

    for file_path in file_paths:
        try:
            with open(file_path, 'rb') as f:
                images_data.append(f.read())
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            raise

    return await oss_storage.upload_images_batch(images_data, user_id)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    async def test_upload():
        """测试上传功能"""
        print("测试 OSS 上传...")

        # 创建测试图片数据
        test_image_data = b"fake image data for testing"

        try:
            url = await oss_storage.upload_single_image(test_image_data, user_id=1)
            print(f"上传成功! URL: {url}")
        except Exception as e:
            print(f"上传失败: {e}")

    # 运行测试
    asyncio.run(test_upload())
