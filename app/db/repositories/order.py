from typing import Dict, List, Optional, Any
from datetime import datetime

from app.db.repositories import BaseRepository
from app.models import Order
from app.utils import convert_mongo_document


class OrderRepository(BaseRepository[Order]):
    """Repository cho collection orders sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Order Repository."""
        super().__init__(Order)

    async def get_orders_by_range_year(
        self, year_start: int, year_end: int
    ) -> List[Dict[str, Any]]:
        """Lấy đơn hàng theo năm"""
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": datetime(year_start, 1, 1),
                        "$lt": datetime(year_end + 1, 1, 1),
                    },
                    "payment_status": {"$in": ["paid", "pending"]},
                    "shipping_status": {"$in": ["shipping", "shipped"]},
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "order_number": 1,
                    "total_price": 1,
                    "total_value_items": 1,
                    "shipping_discount": 1,
                    "shop_id": 1,
                    "user_id": 1,
                    "payment_method_id": 1,
                    "payment_status": 1,
                    "shipping_status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                }
            },
            {
                "$lookup": {
                    "from": "orderitems",
                    "let": {"order_id": "$_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$order_id", "$$order_id"]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "product_id": 1,
                                "quantity": 1,
                                "variant": 1,
                                "product": 1,
                            }
                        },
                    ],
                    "as": "order_items",
                },
            },
        ]

        order_raw = await self.model.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(order_raw)
