import logging
from typing import Optional
import aioredis
from aioredis import Redis

from app.core.config import settings
from app.core.exceptions import RedisException

logger = logging.getLogger(__name__)


class RedisClient:
    """Client kết nối Redis cho ứng dụng."""

    def __init__(self):
        """Khởi tạo Redis client."""
        self.client: Optional[Redis] = None
        self.connection_url = settings.REDIS_URL

    async def connect(self) -> None:
        """
        Kết nối đến Redis server.

        Raises:
            RedisException: Nếu không thể kết nối đến Redis.
        """
        try:
            logger.info(f"Đang kết nối đến Redis tại {self.connection_url}")
            self.client = await aioredis.from_url(
                self.connection_url, encoding="utf-8", decode_responses=True
            )
            logger.info("Kết nối Redis thành công")
        except Exception as e:
            logger.error(f"Không thể kết nối đến Redis: {str(e)}")
            raise RedisException(detail=f"Không thể kết nối đến Redis: {str(e)}")

    async def disconnect(self) -> None:
        """Đóng kết nối Redis."""
        if self.client:
            logger.info("Đóng kết nối Redis")
            await self.client.close()
            self.client = None


# Khởi tạo đối tượng Redis client
redis = RedisClient()
