from app.db.repositories import BaseRepository
from app.models import Shop
from app.utils import convert_mongo_document
from typing import List


class ShopRepository(BaseRepository[Shop]):
    """Repository cho collection order_items sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Shop Repository."""
        super().__init__(Shop)

    async def get_available_shops(self) -> List[str]:
        """Lấy danh sách các shop đang hoạt động."""
        pipeline = [
            {
                "$match": {"is_approved": True, "pause_mode": False},
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
