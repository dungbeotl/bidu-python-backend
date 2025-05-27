from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

from app.db.repositories import BaseRepository
from app.models import Address
from app.utils import convert_mongo_document


class AddressRepository(BaseRepository[Address]):
    """Repository cho collection addresses sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Address Repository."""
        super().__init__(Address)

    async def get_by_user_id(self, user_id: str) -> List[Address]:
        """
        Lấy tất cả địa chỉ của một user.

        Args:
            user_id: ID của user.

        Returns:
            Danh sách các địa chỉ.
        """
        return await Address.find(
            {"accessible_id": user_id, "accessible_type": "User"}
        ).to_list()

    async def get_default_address(self, user_id: str) -> Optional[Address]:
        """
        Lấy địa chỉ mặc định của user.

        Args:
            user_id: ID của user.

        Returns:
            Địa chỉ mặc định nếu có, None nếu không.
        """
        return await Address.find_one(
            {"accessible_id": user_id, "accessible_type": "User", "is_default": True}
        )

    async def get_delivery_default_address(self, user_id: str) -> Optional[Address]:
        """
        Lấy địa chỉ giao hàng mặc định.

        Args:
            user_id: ID của user.

        Returns:
            Địa chỉ giao hàng mặc định nếu có, None nếu không.
        """
        return await Address.find_one(
            {
                "accessible_id": user_id,
                "accessible_type": "User",
                "is_delivery_default": True,
            }
        )

    async def get_all_addresses(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả địa chỉ có is_default là True.
        """
        raw_addresses = await self.model.aggregate(
            [
                {
                    "$match": {
                        "is_default": True,
                    }
                }
            ]
        ).to_list()
        return convert_mongo_document(raw_addresses)
