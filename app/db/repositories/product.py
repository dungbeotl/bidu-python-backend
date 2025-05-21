from typing import Dict, List, Optional, Any
from datetime import datetime

from app.db.repositories import BaseRepository
from app.models import Product
from app.utils import convert_mongo_document


class ProductRepository(BaseRepository[Product]):
    """Repository cho collection products sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Product Repository."""
        super().__init__(Product)

    async def get_products_for_personalize(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_categories: bool = False,
        include_detail_info: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu sản phẩm được định dạng cho AWS Personalize.

        Args:
            limit: Số lượng sản phẩm tối đa (None = tất cả).
            skip: Số sản phẩm bỏ qua.
            filter_dict: Bộ lọc bổ sung.
            include_categories: Thêm thông tin category nếu True.

        Returns:
            Danh sách dữ liệu sản phẩm thô.
        """
        # Xác định pipeline
        pipeline = []

        # Thêm bộ lọc nếu có
        if filter_dict:
            pipeline.append({"$match": filter_dict})

        if include_categories:
            pipeline.append(
                {
                    "$lookup": {
                        "from": "ecategories",
                        "let": {"category_id": "$category_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$_id", "$$category_id"]},
                                },
                            },
                        ],
                        "as": "categories",
                    },
                }
            )

        if include_detail_info:
            pipeline.append(
                {
                    "$lookup": {
                        "from": "productdetailinfos",
                        "let": {"productId": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$product_id", "$$productId"]},
                                },
                            },
                            {
                                "$project": {
                                    "category_info_id": 1,
                                    "values": 1,
                                    "value": 1,
                                }
                            },
                            {
                                "$lookup": {
                                    "from": "categoryinfos",
                                    "let": {"categoryInfoId": "$category_info_id"},
                                    "pipeline": [
                                        {
                                            "$match": {
                                                "$expr": {
                                                    "$eq": ["$_id", "$$categoryInfoId"],
                                                },
                                            },
                                        },
                                        {
                                            "$project": {"_id": 1, "name": 1},
                                        },
                                    ],
                                    "as": "category_info",
                                },
                            },
                        ],
                        "as": "product_details",
                    },
                }
            )
        # Project để chỉ lấy các fields cần thiết
        project_fields = {
            "_id": 1,
            "name": 1,
            "is_approved": 1,
            "deleted_at": 1,
            "before_sale_price": 1,
            "sale_price": 1,
            "categories": 1,
            "product_details": 1,
            "list_category_id": 1,
            "createdAt": 1,
        }

        pipeline.append({"$project": project_fields})

        # Thêm pagination
        if skip > 0:
            pipeline.append({"$skip": skip})

        if limit is not None:
            pipeline.append({"$limit": limit})

        # Thực hiện aggregation với Beanie
        raw_products = await Product.aggregate(pipeline).to_list()
        return convert_mongo_document(raw_products)
