from typing import Dict, List, Optional, Any
import logging

from app.core.exceptions import DatabaseException
from app.db.repositories import ShopRepository
from app.services import BaseService

logger = logging.getLogger(__name__)


class ShopService(BaseService[ShopRepository]):
    """Service for shop operations."""

    def __init__(self):
        """Khởi tạo ShopService."""
        super().__init__(repository=ShopRepository(), es_index="shops")

    async def get_shop_by_ids(self, shop_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Lấy thông tin shop theo danh sách IDs.
        
        Args:
            shop_ids: Danh sách shop IDs cần lấy thông tin
            
        Returns:
            List các dictionary chứa _id và updatedAt
        """
        try:
            shops = await self.repository.get_shop_by_ids(shop_ids)
            return shops
        except Exception as e:
            logger.error(f"Error getting shops by IDs: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi lấy thông tin shop: {str(e)}") 