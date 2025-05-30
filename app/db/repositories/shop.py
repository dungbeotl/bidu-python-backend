from app.db.repositories import BaseRepository
from app.models import Shop
from app.utils import convert_mongo_document
from typing import List, Dict, Any
from bson import ObjectId

class ShopRepository(BaseRepository[Shop]):
    """Repository cho collection order_items sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Shop Repository."""
        super().__init__(Shop)

    async def get_available_shops(self) -> List[str]:
        """Lấy danh sách các shop đang hoạt động."""
        pipeline = [
            {
                "$match": {"is_approved": True},
            },
            {
                "$project": {
                    "_id": 1,
                }
            },
        ]
        raw_shops = await self.model.aggregate(pipeline, allowDiskUse=True).to_list()
        shops = convert_mongo_document(raw_shops)
        return [shop["_id"] for shop in shops]

    async def get_shop_by_ids(self, shop_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Lấy shop theo danh sách IDs, chỉ trả về _id và updatedAt.

        Args:
            shop_ids: Danh sách shop IDs cần lấy thông tin

        Returns:
            List các dictionary chứa _id và updatedAt
        """
        # Chuyển đổi string IDs thành ObjectIds
        object_ids = []
        for shop_id in shop_ids:
            try:
                if ObjectId.is_valid(shop_id):
                    object_ids.append(ObjectId(shop_id))
            except Exception:
                continue

        if not object_ids:
            return []

        pipeline = [
            {"$match": {"_id": {"$in": object_ids}}},
            {
                "$project": {
                    "_id": 1,
                    "updatedAt": 1,
                    "createdAt": 1,
                }
            },
        ]

        raw_shops = await self.model.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_shops)
