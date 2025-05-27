from app.db.repositories import BaseRepository
from app.models import OrderItem
from app.utils import convert_mongo_document
from datetime import datetime
from typing import List, Dict, Any


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository cho collection order_items sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo OrderItem Repository."""
        super().__init__(OrderItem)

    async def get_all_order_items(self):
        """Lấy tất cả các order_items.
        Lookup với bảng 'orders'
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "orders",
                    "let": {"order_id": "$order_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$order_id"]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "shipping_status": 1,
                                "created_at": 1,
                                "payment_status": 1,
                                "deleted_at": 1,
                                "address": 1,
                                "user_id": 1,
                                "shop_id": 1,
                                "payment_method_id": 1,
                            }
                        },
                    ],
                    "as": "order",
                },
            }
        ]
        order_items_raw = await OrderItem.aggregate(
            pipeline, allowDiskUse=True
        ).to_list()
        return convert_mongo_document(order_items_raw)

    async def get_statistic_order_by_range_year(
        self, year_start: int, year_end: int
    ) -> List[Dict[str, Any]]:
        """Lấy thống kê đơn hàng theo năm"""
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": datetime(year_start, 1, 1),
                        "$lt": datetime(year_end + 1, 1, 1),
                    }
                },
            },
            {
                "$lookup": {
                    "from": "orders",
                    "let": {"order_id": "$order_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$and": [
                            {"$eq": ["$_id", "$$order_id"]},
                            {""}
                        ]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "shipping_status": 1,
                                "created_at": 1,
                                "payment_status": 1,
                                "deleted_at": 1,
                                "address": 1,
                                "user_id": 1,
                                "shop_id": 1,
                                "payment_method_id": 1,
                            }
                        },
                    ],
                    "as": "order",
                },
            },
        ]
