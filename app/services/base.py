from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import logging
from beanie import Document

from app.db.repositories.base import BaseRepository
from app.utils.serialization import convert_mongo_document

# Logger
logger = logging.getLogger(__name__)

# Type variables
R = TypeVar("R", bound=BaseRepository)  # Repository type, bound to BaseRepository
T = TypeVar("T", bound=Document)  # Model type, bound to Document


class BaseService(Generic[R]):
    """Base service cho các service khác kế thừa."""

    def __init__(self, repository: R, es_index: Optional[str] = None):
        """
        Khởi tạo BaseService.

        Args:
            repository: Repository instance kế thừa từ BaseRepository.
            es_index: Tên index Elasticsearch (nếu có).
        """
        self.repository = repository
        self.es_index = es_index

    def _prepare_data(self, data: Any) -> Any:
        """
        Chuẩn bị dữ liệu để trả về API.
        Xử lý chuyển đổi ObjectId và Document của Beanie thành JSON-serializable.

        Args:
            data: Dữ liệu từ database (có thể là Document, dict, list, etc.)

        Returns:
            Dữ liệu đã được chuẩn bị sẵn sàng cho JSON serialization.
        """
        if data is None:
            return None

        # Sử dụng hàm convert_mongo_document để xử lý Beanie Document và ObjectId
        return convert_mongo_document(data)

    async def prepare_list_data(
        self, data_list: List[Union[Dict, Document]]
    ) -> List[Dict]:
        """
        Chuẩn bị danh sách dữ liệu để trả về API.

        Args:
            data_list: Danh sách dữ liệu từ database.

        Returns:
            Danh sách dữ liệu đã được chuẩn bị.
        """
        if not data_list:
            return []

        return [self._prepare_data(item) for item in data_list]

    # Các phương thức cơ bản cho service

    async def get_by_id(self, id: str) -> Dict:
        """
        Lấy document theo ID và chuẩn bị dữ liệu để trả về API.

        Args:
            id: ID của document.

        Returns:
            Document đã được chuẩn bị cho API response.
        """
        document = await self.repository.get(id)
        return self._prepare_data(document)

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Dict]:
        """
        Lấy tất cả documents với phân trang và chuẩn bị dữ liệu.

        Args:
            limit: Số document tối đa trả về.
            skip: Số document bỏ qua.

        Returns:
            Danh sách documents đã được chuẩn bị.
        """
        documents = await self.repository.get_all_with_pagination(
            limit=limit, skip=skip
        )
        return self.prepare_list_data(documents)
