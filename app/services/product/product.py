from typing import Dict, List, Optional, Any, Union
import logging
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    BadRequestException,
    DatabaseException,
)
from app.db.repositories import ProductRepository, ECategoryRepository, ShopRepository
from app.services import BaseService
from app.services.product.constant import (
    ProductStatus,
    ApprovalStatus,
    CategoryNames,
    ProcessedProductDetails,
    MAX_CATEGORY_LEVELS,
)
from app.utils import to_timestamp, ExportUtil, to_lower_strip
from app.constants import unknown

logger = logging.getLogger(__name__)


class ProductService(BaseService[ProductRepository]):
    """Service for product operations."""

    def __init__(self):
        """Khởi tạo ProductService."""
        super().__init__(repository=ProductRepository(), es_index="products")

    async def export_products_for_personalize(
        self,
        format: str = "csv",
        limit: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_categories: bool = True,
        include_detail_info: bool = True,
        include_variant: bool = True,
        personalize_format: bool = True,
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
                include_variant=include_variant,
            )
            # Kiểm tra nếu không có dữ liệu
            if not raw_products:
                return {"success": False, "message": "Không có dữ liệu sản phẩm"}

            # Xử lý dữ liệu
            if personalize_format == "custom":
                processed_products = await self._process_products_for_personalize(
                    raw_products
                )
            elif personalize_format == "ecommerce":
                processed_products = await self._process_products_for_ecommerce(
                    raw_products
                )

            # Xử lý xuất theo định dạng
            if format.lower() == "json":
                return await ExportUtil()._export_dataset_to_json(processed_products)
            elif format.lower() == "csv":
                return await ExportUtil()._export_dataset_to_csv(processed_products)
            else:
                raise BadRequestException(
                    detail=f"Định dạng {format} không được hỗ trợ"
                )

        except Exception as e:
            logger.error(f"Error exporting products for personalize: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất dữ liệu sản phẩm: {str(e)}")

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
        flat_categories = await self._get_flat_categories()
        available_shops = await self._get_available_shops()

        processed_products = []
        for product in raw_products:
            try:
                processed_product = await self._process_single_product(
                    product, flat_categories, available_shops
                )
                processed_products.append(processed_product)
            except Exception as e:
                # Log error và tiếp tục xử lý sản phẩm khác
                print(f"Error processing product {product.get('_id', unknown)}: {e}")
                continue

        return processed_products

    async def _get_available_shops(self) -> List[str]:
        """Lấy danh sách các shop có sản phẩm"""
        shop_repository = ShopRepository()
        shops = await shop_repository.get_available_shops()
        return shops

    async def _process_single_product(
        self,
        product: Dict[str, Any],
        flat_categories: List[Dict[str, Any]],
        available_shops: List[str],
    ) -> Dict[str, Any]:
        """Xử lý một sản phẩm đơn lẻ"""

        processed_product = {
            "ITEM_ID": product["_id"],
            "ITEM_STATUS": self._determine_product_status(product, available_shops),
        }

        # Xử lý thông tin chi tiết sản phẩm
        product_details = self._extract_product_details(product)
        processed_product.update(
            {
                "GENDER": to_lower_strip(product_details.gender),
                # "BRAND": to_lower_strip(product_details.brand),
                "ORIGIN": to_lower_strip(product_details.origin),
                "STYLE": to_lower_strip(product_details.style),
                "SEASONS": to_lower_strip(product_details.seasons),
            }
        )
        price_min_max = self.extract_price_info(product)
        processed_product.update({"PRICE_MIN": price_min_max.get("PRICE_MIN")})
        processed_product.update({"PRICE_MAX": price_min_max.get("PRICE_MAX")})

        # Xử lý categories
        self._add_category_info(processed_product, product, flat_categories)

        # Xử lý timestamp
        creation_timestamp = to_timestamp(product.get("createdAt"))
        if creation_timestamp:
            processed_product["TIMESTAMP"] = creation_timestamp

        return processed_product

    def _price_min_max_variants(
        self, variants: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Xác định giá min và max của sản phẩm"""

        result = {
            "sale_price_min_max": {"min": None, "max": None},
            "before_sale_price_min_max": {"min": None, "max": None},
        }

        sale_min = sale_max = None
        before_min = before_max = None

        for item in variants:
            # Xử lý sale_price
            sale_price = item.get("sale_price")
            if sale_price is not None:
                if sale_min is None or sale_price < sale_min:
                    sale_min = sale_price
                if sale_max is None or sale_price > sale_max:
                    sale_max = sale_price

            # Xử lý before_sale_price
            before_price = item.get("before_sale_price")
            if before_price is not None:
                if before_min is None or before_price < before_min:
                    before_min = before_price
                if before_max is None or before_price > before_max:
                    before_max = before_price

        result["sale_price_min_max"]["min"] = sale_min
        result["sale_price_min_max"]["max"] = sale_max
        result["before_sale_price_min_max"]["min"] = before_min
        result["before_sale_price_min_max"]["max"] = before_max

        return result

    def extract_price_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Trích xuất thông tin giá từ sản phẩm"""
        variants = product.get("variants", [])

        if variants:
            # Lấy giá từ variants
            price_variants = self._price_min_max_variants(variants)
            return {
                "PRICE_MIN": price_variants["before_sale_price_min_max"]["min"],
                "PRICE_MAX": price_variants["before_sale_price_min_max"]["max"],
            }
        else:
            # Fallback sang before_sale_price của product
            before_sale_price = product.get("before_sale_price")
            return {
                "PRICE_MIN": before_sale_price,
                "PRICE_MAX": before_sale_price,
            }

    def _price_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Xác định giá sản phẩm"""

        def format_price(value):
            return (
                str(int(value))
                if isinstance(value, (int, float)) and value == int(value)
                else str(value)
            )

        price = None
        variants = product.get("variants", [])
        if variants:
            price_variants = self._price_min_max_variants(variants)
            min_price = price_variants["before_sale_price_min_max"]["min"]
            max_price = price_variants["before_sale_price_min_max"]["max"]

            # if min_price == max_price:
            #     price = format_price(min_price)
            # else:
            price = f"{format_price(min_price)}-{format_price(max_price)}"
        else:
            price_raw = product.get("sale_price")
            price = format_price(price_raw)

        return price

    def _determine_product_status(
        self, product: Dict[str, Any], available_shops: List[str] = []
    ) -> str:
        """Xác định trạng thái sản phẩm"""

        if self._is_product_deleted(product):
            return ProductStatus.DELETED
        elif product.get("shop_id") not in available_shops:
            return ProductStatus.UNAVAILABLE

        approval_status = product.get("is_approved")
        allow_to_sell = product.get("allow_to_sell")
        is_sold_out = product.get("is_sold_out")

        if (
            approval_status == ApprovalStatus.APPROVED
            and allow_to_sell
            and is_sold_out is False
        ):
            return ProductStatus.ACTIVE
        elif approval_status == ApprovalStatus.DRAFT:
            return ProductStatus.DRAFT

        return ProductStatus.UNAVAILABLE

    def _is_product_deleted(self, product: Dict[str, Any]) -> bool:
        """Kiểm tra xem sản phẩm có bị xóa không"""
        return product.get("deleted_at") is not None

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
        # check gender = nữ -> female, gender = nam -> male, gender = unisex -> unisex
        gender = self._join_values(detail_collectors[CategoryNames.GENDER])
        if gender == "Nữ":
            gender = "female"
        elif gender == "Nam":
            gender = "male"
        elif gender == "Unisex":
            gender = "unisex"
        else:
            gender = unknown
        return ProcessedProductDetails(
            gender=gender,
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
        """Join các values thành string, trả về unknown nếu rỗng"""
        if not values:
            return unknown
        return "|".join(values)

    def _add_category_info(
        self,
        processed_product: Dict[str, Any],
        product: Dict[str, Any],
        flat_categories: List[Dict[str, Any]],
    ) -> None:
        """Thêm thông tin category vào processed_product"""
        category_ids = product.get("list_category_id") or []

        # Đảm bảo category_ids là một list
        if not isinstance(category_ids, list):
            category_ids = []

        for level in range(1, MAX_CATEGORY_LEVELS + 1):
            array_index = level - 1
            category_name = self._get_category_name_by_level(
                category_ids, array_index, flat_categories
            )
            processed_product[f"CATEGORY_L{level}"] = to_lower_strip(category_name)

    def _get_category_name_by_level(
        self,
        category_ids: List[str],
        array_index: int,
        flat_categories: List[Dict[str, Any]],
    ) -> str:
        """Lấy tên category theo level"""
        # Kiểm tra an toàn cho category_ids
        if not category_ids or not isinstance(category_ids, list):
            return unknown

        if array_index >= len(category_ids):
            return unknown

        category_id = category_ids[array_index]
        if not category_id:
            return unknown

        category = self.find_category_by_id(flat_categories, category_id)
        return category.get("name", unknown) if category else unknown

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

    # **************************************************
    # Statistics/Analysis Product
    # **************************************************

    async def get_statistics(self) -> List[Dict[str, Any]]:
        """Lấy thống kê sản phẩm có lượt bán cao nhất 'sold'
        Return:
        Tạo file excel gồm có các thông tin:
            - Product ID
            - Product Name
            - Product Shorten Link (Cần nối chuỗi: bidu.vn + shorten_link)
            - Product Sold
            - Product Price (Format: min-max)
            - Product Created At (Format: dd/mm/yyyy)
            - Product Deleted At (Nếu có trả về "Deleted", nếu không trả về "")
            - Product Is Approved (
                Nếu là approved thì trả về "Approved",
                nếu là draft thì trả về "Draft",
                nếu là pending thì trả về "Pending",
            )
            - Product Shop Name (shop[0].user[0].nameOrganizer.userName)
            - Product Shop Shorten Link (Cần nối chuỗi: bidu.vn + shop[0].shorten_link)
        """
        try:
            raw_products = await self.repository.get_all_product_sold()
            processed_products = []

            for product in raw_products:
                try:
                    processed_product = self._process_product_statistics(product)
                    processed_products.append(processed_product)
                except Exception as e:
                    logger.error(
                        f"Error processing product statistics {product.get('_id', 'unknown')}: {e}"
                    )
                    continue

            return processed_products
        except Exception as e:
            logger.error(f"Error getting product statistics: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi lấy thống kê sản phẩm: {str(e)}")

    async def export_statistics_to_excel(self) -> StreamingResponse:
        """
        Xuất thống kê sản phẩm ra file Excel.

        Returns:
            StreamingResponse với file Excel.
        """
        try:
            # Lấy dữ liệu thống kê
            statistics_data = await self.get_statistics()

            # Xuất ra Excel
            export_util = ExportUtil()
            return await export_util._export_dataset_to_excel(
                data=statistics_data, filename_prefix="product_statistics"
            )
        except Exception as e:
            logger.error(f"Error exporting statistics to Excel: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất thống kê ra Excel: {str(e)}")

    def _process_product_statistics(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý dữ liệu sản phẩm cho thống kê"""
        from datetime import datetime

        # Lấy thông tin cơ bản
        product_id = product.get("_id", "")
        product_name = product.get("name", "")
        product_sold = product.get("sold", 0)

        # Xử lý shorten_link
        shorten_link = product.get("shorten_link", "")
        product_link = f"bidu.vn{shorten_link}" if shorten_link else ""

        # Xử lý giá sản phẩm từ variants
        price = None
        variants = product.get("variants", [])
        if variants:
            price_variants = self._price_min_max_variants(variants)
            min_price = price_variants["before_sale_price_min_max"]["min"]
            max_price = price_variants["before_sale_price_min_max"]["max"]

            price = f"{min_price}-{max_price}"
        else:
            price_raw = product.get("before_sale_price")
            price = price_raw

        # Xử lý ngày tạo
        created_at = product.get("createdAt")
        formatted_created_at = ""
        if created_at:
            if isinstance(created_at, str):
                try:
                    date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    formatted_created_at = date_obj.strftime("%d/%m/%Y")
                except:
                    formatted_created_at = ""
            elif isinstance(created_at, datetime):
                formatted_created_at = created_at.strftime("%d/%m/%Y")

        # Xử lý trạng thái xóa
        deleted_status = "Deleted" if product.get("deleted_at") else ""

        # Xử lý trạng thái phê duyệt
        approval_status = product.get("is_approved", "")
        if approval_status == "approved":
            approval_display = "Approved"
        elif approval_status == "draft":
            approval_display = "Draft"
        elif approval_status == "pending":
            approval_display = "Pending"
        elif approval_status == "rejected":
            approval_display = "Rejected"
        else:
            approval_display = approval_status

        # Xử lý thông tin shop
        shop_name = ""
        shop_link = ""

        shops = product.get("shop", [])
        if shops and len(shops) > 0:
            shop = shops[0]
            users = shop.get("user", [])
            if users and len(users) > 0:
                name_organizer = users[0].get("nameOrganizer", {})
                shop_name = name_organizer.get("userName", "")

            shop_shorten_link = shop.get("shorten_link", "")
            shop_link = f"bidu.vn{shop_shorten_link}" if shop_shorten_link else ""

        return {
            "Product ID": product_id,
            "Product Name": product_name,
            "Product Shorten Link": product_link,
            "Product Sold": product_sold,
            "Product Price": price,
            "Product Created At": formatted_created_at,
            "Product Deleted At": deleted_status,
            "Product Is Approved": approval_display,
            "Product Shop Name": shop_name,
            "Product Shop Shorten Link": shop_link,
        }

    def _format_price_from_variants(self, variants: List[Dict[str, Any]]) -> str:
        """Format giá từ variants cho thống kê"""
        if not variants:
            return "N/A"

        # Lấy tất cả giá before_sale_price từ variants
        prices = []
        for variant in variants:
            price = variant.get("before_sale_price")
            if price is not None and price > 0:
                prices.append(price)

        if not prices:
            return "N/A"

        min_price = min(prices)
        max_price = max(prices)

        def format_price(value):
            return (
                str(int(value))
                if isinstance(value, (int, float)) and value == int(value)
                else str(value)
            )

        if min_price == max_price:
            return format_price(min_price)
        else:
            return f"{format_price(min_price)}-{format_price(max_price)}"

    # **************************************************
    # E-commerce format methods for AWS Personalize
    # **************************************************

    def _add_category_info_ecommerce(
        self,
        processed_product: Dict[str, Any],
        product: Dict[str, Any],
        flat_categories: List[Dict[str, Any]],
    ) -> None:
        """Thêm thông tin category L1, L2, L3 cho format ecommerce"""
        category_ids = product.get("list_category_id") or []

        # Đảm bảo category_ids là một list
        if not isinstance(category_ids, list):
            category_ids = []

        # Xử lý 3 levels category
        for level in range(1, 4):  # L1, L2, L3
            array_index = level - 1
            category_name = self._get_category_name_by_level(
                category_ids, array_index, flat_categories
            )
            processed_product[f"CATEGORY_L{level}"] = to_lower_strip(category_name)

    async def _process_single_product_for_ecommerce(
        self,
        product: Dict[str, Any],
        flat_categories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Xử lý một sản phẩm đơn lẻ cho format e-commerce"""

        processed_product = {
            "ITEM_ID": product["_id"],
        }

        # Xử lý thông tin chi tiết sản phẩm để lấy GENDER
        product_details = self._extract_product_details(product)
        processed_product["GENDER"] = to_lower_strip(product_details.gender)

        price = self._extract_min_price(product)
        processed_product["PRICE"] = price

        # Xử lý categories L1, L2, L3
        self._add_category_info_ecommerce(processed_product, product, flat_categories)

        # Xử lý timestamp
        creation_timestamp = to_timestamp(product.get("createdAt"))
        if creation_timestamp:
            processed_product["CREATION_TIMESTAMP"] = creation_timestamp

        return processed_product

    def _extract_min_price(self, product: Dict[str, Any]) -> float:
        """Trích xuất giá min từ sản phẩm"""
        variants = product.get("variants", [])

        if variants:
            # Lấy giá min từ variants
            prices = []
            for variant in variants:
                before_sale_price = variant.get("before_sale_price")
                if before_sale_price is not None and before_sale_price > 0:
                    prices.append(before_sale_price)

            if prices:
                return min(prices)

        # Fallback sang before_sale_price của product
        before_sale_price = product.get("before_sale_price")
        if before_sale_price is not None and before_sale_price > 0:
            return before_sale_price

        return 0.0

    async def _process_products_for_ecommerce(
        self, raw_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Xử lý dữ liệu sản phẩm thô cho định dạng e-commerce AWS Personalize.

        Args:
            raw_products: Danh sách sản phẩm thô từ repository.

        Returns:
            Danh sách sản phẩm đã xử lý cho e-commerce format.
        """
        flat_categories = await self._get_flat_categories()

        processed_products = []
        for product in raw_products:
            try:
                processed_product = await self._process_single_product_for_ecommerce(
                    product, flat_categories
                )
                processed_products.append(processed_product)
            except Exception as e:
                # Log error và tiếp tục xử lý sản phẩm khác
                logger.error(
                    f"Error processing product for e-commerce {product.get('_id', unknown)}: {e}"
                )
                continue

        return processed_products

    async def export_products_for_personalize_ecommerce(
        self,
        format: str = "json",
        limit: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Xuất dữ liệu sản phẩm cho AWS Personalize với format ecommerce đơn giản.

        Args:
            format: Định dạng xuất (json, csv).
            limit: Số lượng sản phẩm tối đa (None = tất cả).
            filter_dict: Bộ lọc bổ sung.

        Returns:
            StreamingResponse với dữ liệu định dạng hoặc dict thông tin.
        """
        try:
            # Lấy dữ liệu từ repository
            products_data = await self.get_products_for_personalize_ecommerce(
                limit=limit, filter_dict=filter_dict
            )

            # Kiểm tra nếu không có dữ liệu
            if not products_data:
                return {"success": False, "message": "Không có dữ liệu sản phẩm"}

            # Sử dụng _prepare_data để đảm bảo tất cả ObjectId đã được xử lý
            processed_data = self._prepare_data(products_data)

            # Xử lý xuất theo định dạng
            if format.lower() == "json":
                return await ExportUtil()._export_dataset_to_json(processed_data)
            elif format.lower() == "csv":
                return await ExportUtil()._export_dataset_to_csv(processed_data)
            else:
                raise BadRequestException(
                    detail=f"Định dạng {format} không được hỗ trợ"
                )

        except Exception as e:
            logger.error(
                f"Error exporting products for personalize ecommerce: {str(e)}"
            )
            raise DatabaseException(
                detail=f"Lỗi khi xuất dữ liệu sản phẩm ecommerce: {str(e)}"
            )

    async def get_products_for_personalize_ecommerce(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu sản phẩm được định dạng cho AWS Personalize với format ecommerce đơn giản.
        Format ecommerce: ITEM_ID, CATEGORY_L1, CATEGORY_L2, CATEGORY_L3, CREATION_TIMESTAMP, GENDER.
        """
        try:
            # Lấy dữ liệu từ repository
            raw_products = await self.repository.get_products_for_personalize_ecommerce(
                limit=limit, filter_dict=filter_dict
            )
            print("Get products for personalize ecommerce: ", len(raw_products))

            # Xử lý dữ liệu
            processed_products = await self._process_products_for_personalize_ecommerce(
                raw_products
            )

            print(
                "Processed products for personalize ecommerce: ",
                len(processed_products),
            )

            return processed_products
        except Exception as e:
            logger.error(f"Error getting products for personalize ecommerce: {str(e)}")
            raise DatabaseException(
                detail=f"Lỗi khi lấy dữ liệu sản phẩm ecommerce: {str(e)}"
            )

    async def _process_products_for_personalize_ecommerce(
        self, raw_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Xử lý dữ liệu sản phẩm thô cho định dạng ecommerce AWS Personalize đơn giản.

        Args:
            raw_products: Danh sách sản phẩm thô từ repository.

        Returns:
            Danh sách sản phẩm đã xử lý cho ecommerce format đơn giản.
        """
        flat_categories = await self._get_flat_categories()

        processed_products = []
        for product in raw_products:
            try:
                processed_product = await self._process_single_product_for_ecommerce(
                    product, flat_categories
                )
                processed_products.append(processed_product)
            except Exception as e:
                # Log error và tiếp tục xử lý sản phẩm khác
                logger.error(
                    f"Error processing product for ecommerce {product.get('_id', unknown)}: {e}"
                )
                continue

        return processed_products
