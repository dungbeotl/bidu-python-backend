import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import io
import logging
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    BadRequestException,
    DatabaseException,
)
from app.db.repositories import ProductRepository, ECategoryRepository
from app.services import BaseService
from app.utils import convert_mongo_document
from app.services.product.constant import (
    ProductStatus,
    ApprovalStatus,
    CategoryNames,
    ProcessedProductDetails,
    DEFAULT_VALUE,
    MAX_CATEGORY_LEVELS,
)

logger = logging.getLogger(__name__)


class ProductService(BaseService[ProductRepository]):
    """Service for product operations."""

    def __init__(self):
        """Khởi tạo ProductService."""
        super().__init__(repository=ProductRepository(), es_index="products")

    async def export_products_for_personalize(
        self,
        format: str = "json",
        limit: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_categories: bool = False,
        include_detail_info: bool = False,
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Xuất dữ liệu sản phẩm cho AWS Personalize.

        Args:
            format: Định dạng xuất (json, csv).
            limit: Số lượng sản phẩm tối đa (None = tất cả).
            filter_dict: Bộ lọc bổ sung.
            include_categories: Thêm thông tin category nếu True.

        Returns:
            StreamingResponse với dữ liệu định dạng hoặc dict thông tin.
        """
        try:
            # Lấy dữ liệu từ repository
            raw_products = await self.repository.get_products_for_personalize(
                limit=limit,
                filter_dict=filter_dict,
                include_categories=include_categories,
                include_detail_info=include_detail_info,
            )
            # Kiểm tra nếu không có dữ liệu
            if not raw_products:
                return {"success": False, "message": "Không có dữ liệu sản phẩm"}

            # Xử lý dữ liệu
            processed_products = await self._process_products_for_personalize(
                raw_products
            )

            # Xử lý xuất theo định dạng
            if format.lower() == "json":
                return await self._export_dataset_to_json(processed_products)
            elif format.lower() == "csv":
                return await self._export_dataset_to_csv(processed_products)
            else:
                raise BadRequestException(
                    detail=f"Định dạng {format} không được hỗ trợ"
                )

        except Exception as e:
            logger.error(f"Error exporting products for personalize: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất dữ liệu sản phẩm: {str(e)}")

    async def _export_dataset_to_json(
        self, data: List[Dict[str, Any]]
    ) -> StreamingResponse:
        """
        Xuất dữ liệu thành JSONL (mỗi record một dòng).

        Args:
            data: Danh sách dữ liệu đã xử lý.

        Returns:
            StreamingResponse với dữ liệu JSON.
        """
        # AWS Personalize yêu cầu mỗi record trên một dòng không có dấu phẩy ở cuối
        jsonl_output = ""
        for item in data:
            jsonl_output += json.dumps(item) + "\n"

        # Trả về response
        return StreamingResponse(
            iter([jsonl_output]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=products_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            },
        )

    # async def _get_flat_categories(self) -> dict:
    #     ecategory_repository = ECategoryRepository()
    #     tree_categories = await ecategory_repository.get_tree_categories()
    #     flat_categories = ecategory_repository.flatten_tree(tree_categories)
    #     return flat_categories

    # def find_category_by_id(self, categories_list, cat_id):
    #     for cat in categories_list:
    #         if cat["id"] == cat_id:
    #             return cat
    #     return None

    # async def _process_products_for_personalize(
    #     self, raw_products: List[Dict[str, Any]]
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Xử lý dữ liệu sản phẩm thô cho định dạng AWS Personalize.

    #     Args:
    #         raw_products: Danh sách sản phẩm thô từ repository.

    #     Returns:
    #         Danh sách sản phẩm đã xử lý cho AWS Personalize.
    #     """
    #     # Lấy tất cả danh mục sản phẩm
    #     flat_categories = await self._get_flat_categories()
    #     # return tree_categories
    #     processed_products = []

    #     for product in raw_products:
    #         item_id = product["_id"]

    #         # Xác định trạng thái sản phẩm
    #         item_status = "PENDING"  # Giá trị mặc định

    #         processed_product = {}

    #         # Kiểm tra nếu sản phẩm đã bị xóa
    #         if "deleted_at" in product and product["deleted_at"] is not None:
    #             item_status = "DELETED"
    #         else:
    #             # Xác định trạng thái dựa trên is_approved
    #             if "is_approved" in product:
    #                 if product["is_approved"] == "approved":
    #                     item_status = "ACTIVE"
    #                 elif product["is_approved"] == "draft":
    #                     item_status = "DRAFT"

    #         # Khởi tạo các giá trị mặc định cho các field mới
    #         gender = "UNKNOWN"
    #         brand = "UNKNOWN"
    #         origin = "UNKNOWN"
    #         style = "UNKNOWN"
    #         seasons = "UNKNOWN"
    #         creation_timestamp = None

    #         # Xử lý timestamp từ createdAt
    #         if "createdAt" in product and product["createdAt"] is not None:
    #             # Chuyển đổi createdAt thành timestamp
    #             if isinstance(product["createdAt"], str):
    #                 # Nếu là string ISO format
    #                 date_str = product["createdAt"].replace("Z", "+00:00")
    #                 creation_timestamp = int(
    #                     datetime.fromisoformat(date_str).timestamp()
    #                 )
    #             elif isinstance(product["createdAt"], datetime):
    #                 # Nếu đã là đối tượng datetime
    #                 creation_timestamp = int(product["createdAt"].timestamp())

    #         # Xử lý product_details để lấy các thông tin cần thiết
    #         if "product_details" in product and product["product_details"]:
    #             # Lưu trữ giá trị cho mỗi loại thông tin
    #             gender_values = []
    #             brand_values = []
    #             origin_values = []
    #             style_values = []
    #             season_values = []

    #             for detail in product["product_details"]:
    #                 if "category_info" in detail and detail["category_info"]:
    #                     category_info = detail["category_info"][0]
    #                     if "name" in category_info and "en" in category_info["name"]:
    #                         category_name_en = category_info["name"]["en"]

    #                         # Lấy giá trị từ trường values hoặc value
    #                         values_to_use = []
    #                         if "values" in detail and detail["values"]:
    #                             values_to_use = [v for v in detail["values"] if v]
    #                         elif "value" in detail and detail["value"]:
    #                             values_to_use = [detail["value"]]

    #                         if values_to_use:
    #                             if category_name_en == "Gender":
    #                                 gender_values.extend(values_to_use)
    #                             elif category_name_en == "Brand":
    #                                 brand_values.extend(values_to_use)
    #                             elif category_name_en == "Origin":
    #                                 origin_values.extend(values_to_use)
    #                             elif category_name_en == "Style":
    #                                 style_values.extend(values_to_use)
    #                             elif category_name_en == "Season":
    #                                 season_values.extend(values_to_use)

    #             # Gán giá trị cuối cùng, nối bằng dấu "|" nếu có nhiều giá trị
    #             if gender_values:
    #                 gender = "|".join(gender_values)
    #             if brand_values:
    #                 brand = "|".join(brand_values)
    #             if origin_values:
    #                 origin = "|".join(origin_values)
    #             if style_values:
    #                 style = "|".join(style_values)
    #             if season_values:
    #                 seasons = "|".join(season_values)

    #         # Xử lý category
    #         category_ids = product.get("list_category_id", [])
    #         for level in range(1, 5):  # Level 1, 2, 3, 4
    #             array_index = level - 1  # Chuyển level thành array index (0, 1, 2, 3)
    #             cate_name = "UNKNOWN"

    #             if array_index < len(category_ids):
    #                 cate_id = category_ids[array_index]
    #                 if cate_id:
    #                     # Tìm category trong flat_categories
    #                     category = self.find_category_by_id(flat_categories, cate_id)
    #                     if category:
    #                         cate_name = category.get("name", "UNKNOWN")

    #             processed_product[f"CATEGORY_L{level}"] = cate_name

    #         # Tạo product record với các field bổ sung
    #         processed_product["ITEM_ID"] = item_id
    #         processed_product["ITEM_STATUS"] = item_status
    #         processed_product["GENDER"] = gender
    #         processed_product["BRAND"] = brand
    #         processed_product["ORIGIN"] = origin
    #         processed_product["STYLE"] = style
    #         processed_product["SEASONS"] = seasons

    #         # Thêm CREATION_TIMESTAMP nếu có
    #         if creation_timestamp:
    #             processed_product["CREATION_TIMESTAMP"] = creation_timestamp

    #         processed_products.append(processed_product)

    #     return processed_products

    async def _export_dataset_to_csv(
        self, data: List[Dict[str, Any]]
    ) -> StreamingResponse:
        """
        Xuất dữ liệu thành CSV.

        Args:
            data: Danh sách dữ liệu đã xử lý.

        Returns:
            StreamingResponse với dữ liệu CSV.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Viết header
        if data:
            writer.writerow(data[0].keys())

        # Viết dữ liệu
        for item in data:
            writer.writerow(item.values())

        # Reset về đầu file
        output.seek(0)

        # Trả về response
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=products_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )

    async def _process_products_for_personalize(
        self, raw_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Xử lý dữ liệu sản phẩm thô cho định dạng AWS Personalize.

        Args:
            raw_products: Danh sách sản phẩm thô từ repository.

        Returns:
            Danh sách sản phẩm đã xử lý cho AWS Personalize.
        """
        self.flat_categories = await self._get_flat_categories()

        processed_products = []
        for product in raw_products:
            try:
                processed_product = self._process_single_product(product)
                processed_products.append(processed_product)
            except Exception as e:
                # Log error và tiếp tục xử lý sản phẩm khác
                print(f"Error processing product {product.get('_id', 'Unknown')}: {e}")
                continue

        return processed_products

    def _process_single_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý một sản phẩm đơn lẻ"""
        processed_product = {
            "ITEM_ID": product["_id"],
            "ITEM_STATUS": self._determine_product_status(product),
        }

        # Xử lý thông tin chi tiết sản phẩm
        product_details = self._extract_product_details(product)
        processed_product.update(
            {
                "GENDER": product_details.gender,
                "BRAND": product_details.brand,
                "ORIGIN": product_details.origin,
                "STYLE": product_details.style,
                "SEASONS": product_details.seasons,
            }
        )

        # Xử lý categories
        self._add_category_info(processed_product, product)

        # Xử lý timestamp
        creation_timestamp = self._extract_creation_timestamp(product)
        if creation_timestamp:
            processed_product["CREATION_TIMESTAMP"] = creation_timestamp

        return processed_product

    def _determine_product_status(self, product: Dict[str, Any]) -> str:
        """Xác định trạng thái sản phẩm"""
        if self._is_product_deleted(product):
            return ProductStatus.DELETED

        approval_status = product.get("is_approved")
        if approval_status == ApprovalStatus.APPROVED:
            return ProductStatus.ACTIVE
        elif approval_status == ApprovalStatus.DRAFT:
            return ProductStatus.DRAFT

        return ProductStatus.PENDING

    def _is_product_deleted(self, product: Dict[str, Any]) -> bool:
        """Kiểm tra xem sản phẩm có bị xóa không"""
        return product.get("deleted_at") is not None

    def _extract_creation_timestamp(self, product: Dict[str, Any]) -> Optional[int]:
        """Trích xuất timestamp từ createdAt"""
        created_at = product.get("createdAt")
        if not created_at:
            return None

        try:
            if isinstance(created_at, str):
                # Xử lý ISO format string
                date_str = created_at.replace("Z", "+00:00")
                return int(datetime.fromisoformat(date_str).timestamp())
            elif isinstance(created_at, datetime):
                return int(created_at.timestamp())
        except (ValueError, AttributeError) as e:
            print(f"Error parsing timestamp {created_at}: {e}")

        return None

    def _extract_product_details(
        self, product: Dict[str, Any]
    ) -> ProcessedProductDetails:
        """Trích xuất thông tin chi tiết từ product_details"""
        product_details_list = product.get("product_details", [])
        if not product_details_list:
            return ProcessedProductDetails()

        # Khởi tạo các collectors cho từng loại thông tin
        detail_collectors = {
            CategoryNames.GENDER: [],
            CategoryNames.BRAND: [],
            CategoryNames.ORIGIN: [],
            CategoryNames.STYLE: [],
            CategoryNames.SEASON: [],
        }

        # Thu thập thông tin từ tất cả product_details
        for detail in product_details_list:
            category_name = self._get_category_name_from_detail(detail)
            if category_name in detail_collectors:
                values = self._extract_values_from_detail(detail)
                if values:
                    detail_collectors[category_name].extend(values)

        # Tạo ProcessedProductDetails với các giá trị đã join
        return ProcessedProductDetails(
            gender=self._join_values(detail_collectors[CategoryNames.GENDER]),
            brand=self._join_values(detail_collectors[CategoryNames.BRAND]),
            origin=self._join_values(detail_collectors[CategoryNames.ORIGIN]),
            style=self._join_values(detail_collectors[CategoryNames.STYLE]),
            seasons=self._join_values(detail_collectors[CategoryNames.SEASON]),
        )

    def _get_category_name_from_detail(self, detail: Dict[str, Any]) -> Optional[str]:
        """Lấy tên category từ detail"""
        try:
            category_info = detail.get("category_info", [])
            if not category_info:
                return None

            first_category = category_info[0]
            name_info = first_category.get("name", {})
            return name_info.get("en")
        except (IndexError, KeyError, TypeError):
            return None

    def _extract_values_from_detail(self, detail: Dict[str, Any]) -> List[str]:
        """Trích xuất values từ detail"""
        # Ưu tiên 'values' trước, sau đó là 'value'
        if detail.get("values"):
            return [str(v) for v in detail["values"] if v]
        elif detail.get("value"):
            return [str(detail["value"])]
        return []

    def _join_values(self, values: List[str]) -> str:
        """Join các values thành string, trả về DEFAULT_VALUE nếu rỗng"""
        if not values:
            return DEFAULT_VALUE
        return "|".join(values)

    def _add_category_info(
        self, processed_product: Dict[str, Any], product: Dict[str, Any]
    ) -> None:
        """Thêm thông tin category vào processed_product"""
        category_ids = product.get("list_category_id", [])

        for level in range(1, MAX_CATEGORY_LEVELS + 1):
            array_index = level - 1
            category_name = self._get_category_name_by_level(category_ids, array_index)
            processed_product[f"CATEGORY_L{level}"] = category_name

    def _get_category_name_by_level(
        self, category_ids: List[str], array_index: int
    ) -> str:
        """Lấy tên category theo level"""
        if array_index >= len(category_ids):
            return DEFAULT_VALUE

        category_id = category_ids[array_index]
        if not category_id:
            return DEFAULT_VALUE

        category = self.find_category_by_id(self.flat_categories, category_id)
        return category.get("name", DEFAULT_VALUE) if category else DEFAULT_VALUE

    async def _get_flat_categories(self) -> List[Dict[str, Any]]:
        """Lấy danh sách categories phẳng - cần implement"""
        ecategory_repository = ECategoryRepository()
        tree_categories = await ecategory_repository.get_tree_categories()
        flat_categories = ecategory_repository.flatten_tree(tree_categories)
        return flat_categories

    def find_category_by_id(
        self, categories: List[Dict[str, Any]], category_id: str
    ) -> Optional[Dict[str, Any]]:
        """Tìm category theo ID - cần implement"""
        for cat in categories:
            if cat["id"] == category_id:
                return cat
        return None
