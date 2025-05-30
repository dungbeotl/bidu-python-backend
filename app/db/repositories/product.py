from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

from app.db.repositories import BaseRepository, ShopRepository
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
        include_variant: bool = False,
        include_available_shop: bool = False,
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
        pipeline = [
            {
                "$match": {
                    "is_approved": {"$in": ["approved"]},
                    "deleted_at": None,
                    "allow_to_sell": True,
                    "is_sold_out": False,
                    "quantity": {"$gt": 0},
                }
            }
        ]

        if include_available_shop:
            shop_repository = ShopRepository()
            available_shops = await shop_repository.get_available_shops()
            pipeline.append({"$match": {"shop_id": {"$in": [ObjectId(available_shop) for available_shop in available_shops]}}})

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

        if include_variant:
            pipeline.append(
                {
                    "$lookup": {
                        "from": "variants",
                        "let": {"product_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$product_id", "$$product_id"]},
                                },
                            },
                        ],
                        "as": "variants",
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
            "variants": 1,
            "shop_id": 1,
            "allow_to_sell": 1,
            "is_sold_out": 1,
        }

        pipeline.append({"$project": project_fields})

        # Thêm pagination
        if skip > 0:
            pipeline.append({"$skip": skip})

        if limit is not None:
            pipeline.append({"$limit": limit})

        # Thực hiện aggregation với Beanie
        raw_products = await Product.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_products)

    async def get_all_product_sold(self) -> List[Dict[str, Any]]:
        """Lấy tất cả sản phẩm có lượt bán cao nhất"""
        pipeline = [
            {"$sort": {"sold": -1}},
            {"$limit": 100},
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "sold": 1,
                    "shorten_link": 1,
                    "is_approved": 1,
                    "createdAt": 1,
                    "deleted_at": 1,
                    "shop_id": 1,
                    "before_sale_price": 1,
                }
            },
            {
                "$lookup": {
                    "from": "variants",
                    "let": {"product_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$product_id", "$$product_id"]},
                            },
                        },
                    ],
                    "as": "variants",
                },
            },
            {
                "$lookup": {
                    "from": "shops",
                    "let": {"shop_id": "$shop_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$_id", "$$shop_id"]},
                            },
                        },
                        {
                            "$project": {
                                "user_id": 1,
                                "shorten_link": 1,
                            }
                        },
                        {
                            "$lookup": {
                                "from": "users",
                                "let": {"user_id": "$user_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {"$eq": ["$_id", "$$user_id"]},
                                        },
                                    },
                                    {
                                        "$project": {
                                            "nameOrganizer": 1,
                                        }
                                    },
                                ],
                                "as": "user",
                            }
                        },
                    ],
                    "as": "shop",
                }
            },
        ]

        raw_products = await self.model.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_products)

    async def get_all_product_info(
        self, product_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Lấy thông tin chi tiết các sản phẩm theo danh sách product_ids"""
        from bson import ObjectId

        # Chuyển đổi string IDs thành ObjectIds
        object_ids = []
        for product_id in product_ids:
            try:
                if ObjectId.is_valid(product_id):
                    object_ids.append(ObjectId(product_id))
            except Exception:
                continue

        if not object_ids:
            return []

        pipeline = [
            {
                "$match": {
                    "_id": {"$in": object_ids},
                },
            },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "sold": 1,
                    "shorten_link": 1,
                    "is_approved": 1,
                    "createdAt": 1,
                    "deleted_at": 1,
                    "shop_id": 1,
                    "before_sale_price": 1,
                }
            },
            {
                "$lookup": {
                    "from": "variants",
                    "let": {"product_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$product_id", "$$product_id"]},
                            },
                        },
                    ],
                    "as": "variants",
                },
            },
            {
                "$lookup": {
                    "from": "shops",
                    "let": {"shop_id": "$shop_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$_id", "$$shop_id"]},
                            },
                        },
                        {
                            "$project": {
                                "user_id": 1,
                                "shorten_link": 1,
                            }
                        },
                        {
                            "$lookup": {
                                "from": "users",
                                "let": {"user_id": "$user_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {"$eq": ["$_id", "$$user_id"]},
                                        },
                                    },
                                    {
                                        "$project": {
                                            "nameOrganizer": 1,
                                        }
                                    },
                                ],
                                "as": "user",
                            }
                        },
                    ],
                    "as": "shop",
                }
            },
        ]

        raw_products = await self.model.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_products)

    async def get_products_for_personalize_ecommerce(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu sản phẩm được định dạng cho AWS Personalize với format ecommerce đơn giản.

        Args:
            limit: Số lượng sản phẩm tối đa (None = tất cả).
            skip: Số sản phẩm bỏ qua.
            filter_dict: Bộ lọc bổ sung.

        Returns:
            Danh sách dữ liệu sản phẩm thô cho format ecommerce.
        """
        # Xác định pipeline
        pipeline = [
            {
                "$match": {
                    "is_approved": {"$in": ["approved", "pending"]},
                }
            }
        ]

        # Thêm bộ lọc nếu có
        if filter_dict:
            pipeline.append({"$match": filter_dict})

        # Lookup product details để lấy thông tin GENDER
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

        # Project để chỉ lấy các fields cần thiết cho ecommerce format
        project_fields = {
            "_id": 1,
            "list_category_id": 1,
            "createdAt": 1,
            "product_details": 1,
        }

        pipeline.append({"$project": project_fields})

        # Thêm pagination
        if skip > 0:
            pipeline.append({"$skip": skip})

        if limit is not None:
            pipeline.append({"$limit": limit})

        # Thực hiện aggregation với Beanie
        raw_products = await Product.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_products)
