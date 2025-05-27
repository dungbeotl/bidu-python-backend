y  # app/services/base_redis.py

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Callable
import json
import logging
import pickle
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.db.redis_db import redis

# Type variable cho Model
M = TypeVar("M", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseRedisService(Generic[M]):
    """Base service cho Redis."""

    def __init__(
        self, prefix: str, model: Type[M], default_ttl: Optional[int] = None
    ):
        """
        Khởi tạo Redis service.

        Args:
            prefix: Tiền tố cho cache key.
            model: Pydantic model class.
            default_ttl: Thời gian sống mặc định của cache key (giây).
                         Nếu không có, sử dụng REDIS_TTL từ settings.
        """
        self.prefix = prefix
        self.model = model
        self.default_ttl = default_ttl or settings.REDIS_TTL
        self.client = redis.client

    def _format_key(self, key: str) -> str:
        """
        Format cache key với prefix.

        Args:
            key: Cache key gốc.

        Returns:
            Cache key với prefix.
        """
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Lấy dữ liệu từ Redis.

        Args:
            key: Cache key.

        Returns:
            Dữ liệu từ Redis nếu tìm thấy, None nếu không tìm thấy.
        """
        try:
            formatted_key = self._format_key(key)
            value = await self.client.get(formatted_key)

            if value is None:
                return None

            try:
                # Thử parse JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Nếu không phải JSON, trả về nguyên giá trị
                return value
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Lưu dữ liệu vào Redis.

        Args:
            key: Cache key.
            value: Giá trị cần lưu.
            ttl: Thời gian sống của key (giây). Nếu không có, sử dụng default_ttl.
            nx: Chỉ set nếu key không tồn tại.
            xx: Chỉ set nếu key đã tồn tại.

        Returns:
            True nếu set thành công, False nếu thất bại.
        """
        try:
            formatted_key = self._format_key(key)

            # Xử lý các loại dữ liệu
            if isinstance(value, (dict, list, tuple, set)):
                value = json.dumps(value)
            elif isinstance(value, BaseModel):
                value = json.dumps(value.model_dump())
            elif not isinstance(value, (str, int, float, bool)):
                value = str(value)

            # Thiết lập TTL
            if ttl is None:
                ttl = self.default_ttl

            # Set với các options
            if nx and xx:
                return False  # Không thể cả nx và xx cùng lúc
            elif nx:
                return await self.client.set(formatted_key, value, ex=ttl, nx=True)
            elif xx:
                return await self.client.set(formatted_key, value, ex=ttl, xx=True)
            else:
                return await self.client.set(formatted_key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Xóa key khỏi Redis.

        Args:
            key: Cache key.

        Returns:
            True nếu xóa thành công, False nếu thất bại.
        """
        try:
            formatted_key = self._format_key(key)
            result = await self.client.delete(formatted_key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Kiểm tra xem key có tồn tại trong Redis không.

        Args:
            key: Cache key.

        Returns:
            True nếu key tồn tại, False nếu không.
        """
        try:
            formatted_key = self._format_key(key)
            result = await self.client.exists(formatted_key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking if key {key} exists in Redis: {str(e)}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Thiết lập thời gian sống cho key.

        Args:
            key: Cache key.
            ttl: Thời gian sống (giây).

        Returns:
            True nếu thiết lập thành công, False nếu thất bại.
        """
        try:
            formatted_key = self._format_key(key)
            result = await self.client.expire(formatted_key, ttl)
            return result > 0
        except Exception as e:
            logger.error(f"Error setting expiry for key {key} in Redis: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Lấy thời gian sống còn lại của key.

        Args:
            key: Cache key.

        Returns:
            Thời gian sống còn lại (giây), -1 nếu key không có expiry, -2 nếu key không tồn tại.
        """
        try:
            formatted_key = self._format_key(key)
            return await self.client.ttl(formatted_key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} from Redis: {str(e)}")
            return -2

    async def clear_prefix(self, pattern: str = "*") -> int:
        """
        Xóa tất cả các key có prefix và pattern cụ thể.

        Args:
            pattern: Pattern để lọc key.

        Returns:
            Số lượng key đã xóa.
        """
        try:
            formatted_pattern = self._format_key(pattern)
            keys = await self.client.keys(formatted_pattern)

            if not keys:
                return 0

            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(
                f"Error clearing keys with pattern {pattern} from Redis: {str(e)}"
            )
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Tăng giá trị của key.

        Args:
            key: Cache key.
            amount: Lượng tăng.

        Returns:
            Giá trị mới sau khi tăng.
        """
        try:
            formatted_key = self._format_key(key)
            return await self.client.incrby(formatted_key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in Redis: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi tăng giá trị key: {str(e)}")

    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Giảm giá trị của key.

        Args:
            key: Cache key.
            amount: Lượng giảm.

        Returns:
            Giá trị mới sau khi giảm.
        """
        try:
            formatted_key = self._format_key(key)
            return await self.client.decrby(formatted_key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key} in Redis: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi giảm giá trị key: {str(e)}")

    async def set_list(
        self, key: str, values: List[Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu danh sách vào Redis.

        Args:
            key: Cache key.
            values: Danh sách giá trị.
            ttl: Thời gian sống (giây).

        Returns:
            True nếu set thành công, False nếu thất bại.
        """
        try:
            formatted_key = self._format_key(key)

            # Xử lý các phần tử là object
            processed_values = []
            for value in values:
                if isinstance(value, dict):
                    processed_values.append(json.dumps(value))
                elif isinstance(value, BaseModel):
                    processed_values.append(json.dumps(value.model_dump()))
                else:
                    processed_values.append(str(value))

            # Xóa list cũ nếu có
            await self.client.delete(formatted_key)

            # Thêm các phần tử mới
            if processed_values:
                await self.client.rpush(formatted_key, *processed_values)

            # Thiết lập TTL
            if ttl is None:
                ttl = self.default_ttl

            await self.client.expire(formatted_key, ttl)

            return True
        except Exception as e:
            logger.error(f"Error setting list for key {key} in Redis: {str(e)}")
            return False

    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Lấy danh sách từ Redis.

        Args:
            key: Cache key.
            start: Vị trí bắt đầu.
            end: Vị trí kết thúc (-1 là đến cuối).

        Returns:
            Danh sách giá trị.
        """
        try:
            formatted_key = self._format_key(key)
            values = await self.client.lrange(formatted_key, start, end)

            # Thử parse JSON cho các phần tử
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)

            return result
        except Exception as e:
            logger.error(f"Error getting list for key {key} from Redis: {str(e)}")
            return []

    async def set_hash(
        self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu hash vào Redis.

        Args:
            key: Cache key.
            mapping: Dictionary chứa các field và value.
            ttl: Thời gian sống (giây).

        Returns:
            True nếu set thành công, False nếu thất bại.
        """
        try:
            if not mapping:
                return False

            formatted_key = self._format_key(key)

            # Xử lý các giá trị là object
            processed_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list, tuple, set)):
                    processed_mapping[field] = json.dumps(value)
                elif isinstance(value, BaseModel):
                    processed_mapping[field] = json.dumps(value.model_dump())
                elif not isinstance(value, (str, int, float, bool)):
                    processed_mapping[field] = str(value)
                else:
                    processed_mapping[field] = value

            # Set hash
            await self.client.hset(formatted_key, mapping=processed_mapping)

            # Thiết lập TTL
            if ttl is None:
                ttl = self.default_ttl

            await self.client.expire(formatted_key, ttl)

            return True
        except Exception as e:
            logger.error(f"Error setting hash for key {key} in Redis: {str(e)}")
            return False

    async def get_hash(self, key: str) -> Dict[str, Any]:
        """
        Lấy hash từ Redis.

        Args:
            key: Cache key.

        Returns:
            Dictionary chứa các field và value.
        """
        try:
            formatted_key = self._format_key(key)
            hash_data = await self.client.hgetall(formatted_key)

            # Thử parse JSON cho các giá trị
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field] = value

            return result
        except Exception as e:
            logger.error(f"Error getting hash for key {key} from Redis: {str(e)}")
            return {}

    async def get_hash_field(self, key: str, field: str) -> Optional[Any]:
        """
        Lấy giá trị của một field trong hash.

        Args:
            key: Cache key.
            field: Tên field.

        Returns:
            Giá trị của field, None nếu không tìm thấy.
        """
        try:
            formatted_key = self._format_key(key)
            value = await self.client.hget(formatted_key, field)

            if value is None:
                return None

            try:
                # Thử parse JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Nếu không phải JSON, trả về nguyên giá trị
                return value
        except Exception as e:
            logger.error(
                f"Error getting hash field {field} for key {key} from Redis: {str(e)}"
            )
            return None

    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        """
        Lấy lock để xử lý độc quyền.

        Args:
            key: Cache key.
            ttl: Thời gian sống của lock (giây).

        Returns:
            True nếu lấy lock thành công, False nếu thất bại.
        """
        try:
            lock_key = self._format_key(f"lock:{key}")
            return await self.client.set(lock_key, "1", ex=ttl, nx=True)
        except Exception as e:
            logger.error(f"Error acquiring lock for key {key} in Redis: {str(e)}")
            return False

    async def release_lock(self, key: str) -> bool:
        """
        Giải phóng lock.

        Args:
            key: Cache key.

        Returns:
            True nếu giải phóng thành công, False nếu thất bại.
        """
        try:
            lock_key = self._format_key(f"lock:{key}")
            result = await self.client.delete(lock_key)
            return result > 0
        except Exception as e:
            logger.error(f"Error releasing lock for key {key} in Redis: {str(e)}")
            return False

    async def set_with_lock(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu dữ liệu vào Redis với lock để tránh race condition.

        Args:
            key: Cache key.
            value: Giá trị cần lưu.
            ttl: Thời gian sống của key (giây).

        Returns:
            True nếu set thành công, False nếu thất bại.
        """
        lock_acquired = await self.acquire_lock(key)

        if not lock_acquired:
            return False

        try:
            result = await self.set(key, value, ttl)
            return result
        finally:
            await self.release_lock(key)

    async def get_or_set(
        self, key: str, default_fn: Callable[[], Any], ttl: Optional[int] = None
    ) -> Any:
        """
        Lấy giá trị từ Redis, nếu không có thì set giá trị mặc định.

        Args:
            key: Cache key.
            default_fn: Hàm để lấy giá trị mặc định nếu key không tồn tại.
            ttl: Thời gian sống của key (giây).

        Returns:
            Giá trị từ Redis hoặc giá trị mặc định.
        """
        # Thử lấy từ cache
        value = await self.get(key)

        # Nếu có trong cache, trả về luôn
        if value is not None:
            return value

        # Thử lấy lock
        lock_acquired = await self.acquire_lock(key)

        try:
            # Nếu không lấy được lock, có thể người khác đang tính toán
            # Thử lấy lại từ cache một lần nữa
            if not lock_acquired:
                value = await self.get(key)
                if value is not None:
                    return value

            # Nếu vẫn không có, tính toán giá trị mặc định
            default_value = default_fn()

            # Nếu lấy được lock, lưu vào cache
            if lock_acquired:
                await self.set(key, default_value, ttl)

            return default_value
        finally:
            # Giải phóng lock nếu đã lấy được
            if lock_acquired:
                await self.release_lock(key)

    async def cached(
        self,
        key_prefix: str,
        fn: Callable[..., Any],
        *args,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        Decorator để cache kết quả của hàm.

        Args:
            key_prefix: Tiền tố cho cache key.
            fn: Hàm cần cache kết quả.
            *args: Tham số của hàm.
            ttl: Thời gian sống của cache (giây).
            **kwargs: Tham số của hàm.

        Returns:
            Kết quả của hàm.
        """
        # Tạo cache key từ tên hàm và tham số
        key_parts = [key_prefix, fn.__name__]

        # Thêm args vào key
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))

        # Thêm kwargs vào key
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")

        # Tạo cache key
        cache_key = ":".join(key_parts)

        # Thử lấy từ cache
        cached_result = await self.get(cache_key)

        # Nếu có trong cache, trả về luôn
        if cached_result is not None:
            return cached_result

        # Nếu không có, tính toán kết quả
        result = fn(*args, **kwargs)

        # Lưu vào cache
        await self.set(cache_key, result, ttl)

        return result
