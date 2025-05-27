from typing import Dict, List, Optional, Any, Union
import logging
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    BadRequestException,
    DatabaseException,
)
from app.db.repositories import OrderRepository, ProductRepository
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


class OrderService(BaseService[OrderRepository]):
    """Service for order operations."""

    def __init__(self):
        """Khởi tạo OrderService."""
        super().__init__(repository=OrderRepository())
        
    async def get_statistics_order_by_range_year(self, year_start: int, year_end: int, limit_per_year: int = 50) -> Dict[str, Any]:
        """Lấy thống kê top sản phẩm bán chạy theo từng năm"""
        try:
            # Lấy dữ liệu đơn hàng theo khoảng năm
            orders = await self.repository.get_orders_by_range_year(year_start, year_end)
            
            # Xử lý dữ liệu để tính toán lượt bán theo từng năm
            yearly_statistics = self._process_yearly_product_statistics(orders, year_start, year_end, limit_per_year)
            
            return yearly_statistics
        except Exception as e:
            logger.error(f"Error getting yearly product statistics: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi lấy thống kê sản phẩm theo năm: {str(e)}")

    def _process_yearly_product_statistics(self, orders: List[Dict[str, Any]], year_start: int, year_end: int, limit_per_year: int = 50) -> Dict[str, Any]:
        """Xử lý dữ liệu đơn hàng để tính toán lượt bán sản phẩm theo từng năm"""
        from datetime import datetime
        
        # Khởi tạo structure cho kết quả trả về
        result = {}
        
        # Tạo các năm trong khoảng
        for year in range(year_start, year_end + 1):
            result[str(year)] = {}
        
        # Xử lý từng đơn hàng
        for order in orders:
            try:
                # Lấy năm từ createdAt của đơn hàng
                created_at = order.get("created_at")
                if not created_at:
                    continue
                
                # Xử lý các định dạng ngày khác nhau
                order_year = None
                if isinstance(created_at, str):
                    try:
                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        order_year = date_obj.year
                    except:
                        continue
                elif isinstance(created_at, datetime):
                    order_year = created_at.year
                else:
                    continue
                
                # Kiểm tra năm có trong khoảng không
                if order_year < year_start or order_year > year_end:
                    continue
                
                year_key = str(order_year)
                
                # Xử lý từng order_item trong đơn hàng
                order_items = order.get("order_items", [])
                for order_item in order_items:
                    product_id = order_item.get("product_id")
                    quantity = order_item.get("quantity", 0)
                    
                    if not product_id or quantity <= 0:
                        continue
                    
                    product_id_str = str(product_id)
                    
                    # Cập nhật số lượng bán của sản phẩm trong năm
                    if product_id_str not in result[year_key]:
                        result[year_key][product_id_str] = {
                            "product_id": product_id_str,
                            "total_sold": 0
                        }
                    
                    result[year_key][product_id_str]["total_sold"] += quantity
                    
            except Exception as e:
                logger.error(f"Error processing order {order.get('_id', 'unknown')}: {e}")
                continue
        
        # Chuyển từ dict sang list và sắp xếp theo lượt bán giảm dần cho mỗi năm
        for year_key in result:
            # Chuyển từ dict sang list
            products_list = list(result[year_key].values())
            
            # Sắp xếp theo total_sold giảm dần
            products_list.sort(key=lambda x: x["total_sold"], reverse=True)
            
            # Giới hạn số lượng sản phẩm theo tham số
            result[year_key] = products_list[:limit_per_year]
        
        return result

    async def get_statistics_with_product_info_by_year(self, year_start: int, year_end: int, limit_per_year: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Lấy thống kê sản phẩm bán chạy theo năm với thông tin chi tiết sản phẩm"""
        try:
            # Lấy thống kê cơ bản theo năm
            yearly_statistics = await self.get_statistics_order_by_range_year(year_start, year_end, limit_per_year)
            
            # Tập hợp tất cả product_ids để lấy thông tin chi tiết
            all_product_ids = set()
            for year_data in yearly_statistics.values():
                for product_stat in year_data:
                    all_product_ids.add(product_stat["product_id"])
            
            # Lấy thông tin chi tiết sản phẩm
            product_repository = ProductRepository()
            product_infos = await product_repository.get_all_product_info(list(all_product_ids))
            
            # Tạo dict để tra cứu nhanh thông tin sản phẩm
            product_info_dict = {str(product["_id"]): product for product in product_infos}
            
            # Kết hợp dữ liệu thống kê với thông tin sản phẩm
            result = {}
            for year, products_stats in yearly_statistics.items():
                result[year] = []
                for product_stat in products_stats:
                    product_id = product_stat["product_id"]
                    total_sold = product_stat["total_sold"]
                    
                    # Lấy thông tin sản phẩm
                    product_info = product_info_dict.get(product_id)
                    if product_info:
                        # Xử lý thông tin sản phẩm với total_sold từ thống kê
                        processed_product = self._process_product_with_statistics(
                            product_info, total_sold, year
                        )
                        result[year].append(processed_product)
            
            return result
        except Exception as e:
            logger.error(f"Error getting product statistics with info by year: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi lấy thống kê sản phẩm với thông tin chi tiết: {str(e)}")

    def _process_product_with_statistics(self, product: Dict[str, Any], total_sold: int, year: str) -> Dict[str, Any]:
        """Xử lý dữ liệu sản phẩm kết hợp với thống kê bán hàng"""
        from datetime import datetime
        
        # Lấy thông tin cơ bản
        product_id = product.get("_id", "")
        product_name = product.get("name", "")
        
        # Xử lý shorten_link
        shorten_link = product.get("shorten_link", "")
        product_link = f"bidu.vn{shorten_link}" if shorten_link else ""
        
        # Xử lý giá sản phẩm từ variants
        price = "N/A"
        variants = product.get("variants", [])
        if variants:
            # Sử dụng logic giống như trong ProductService
            prices = []
            for variant in variants:
                variant_price = variant.get("before_sale_price")
                if variant_price is not None and variant_price > 0:
                    prices.append(variant_price)
            
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                
                def format_price(value):
                    return str(int(value)) if isinstance(value, (int, float)) and value == int(value) else str(value)
                
                if min_price == max_price:
                    price = format_price(min_price)
                else:
                    price = f"{format_price(min_price)}-{format_price(max_price)}"
        else:
            # Fallback sang before_sale_price của product
            price_raw = product.get("before_sale_price")
            if price_raw and price_raw > 0:
                price = str(int(price_raw)) if price_raw == int(price_raw) else str(price_raw)
        
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
            "Year": year,
            "Product ID": product_id,
            "Product Name": product_name,
            "Product Shorten Link": product_link,
            "Product Sold": total_sold,  # Sử dụng total_sold từ thống kê
            "Product Price": price,
            "Product Created At": formatted_created_at,
            "Product Deleted At": deleted_status,
            "Product Is Approved": approval_display,
            "Product Shop Name": shop_name,
            "Product Shop Shorten Link": shop_link,
        }

    async def export_statistics_with_product_info_to_excel(self, year_start: int, year_end: int, limit_per_year: int = 50) -> StreamingResponse:
        """
        Xuất thống kê sản phẩm bán chạy theo năm với thông tin chi tiết ra Excel với nhiều sheet.
        
        Args:
            year_start: Năm bắt đầu
            year_end: Năm kết thúc  
            limit_per_year: Số lượng sản phẩm tối đa mỗi năm (mặc định 50, tối đa 1000)
            
        Returns:
            StreamingResponse với file Excel chứa nhiều sheet (mỗi năm 1 sheet).
        """
        try:
            # Lấy dữ liệu thống kê với thông tin sản phẩm
            yearly_data = await self.get_statistics_with_product_info_by_year(year_start, year_end, limit_per_year)
            
            # Chuẩn bị dữ liệu cho multiple sheets
            sheets_data = {}
            
            # Tạo sheet cho từng năm
            for year, products in yearly_data.items():
                sheet_name = f"Year {year}"
                sheets_data[sheet_name] = products
            
            # Tạo sheet tổng hợp tất cả các năm
            all_data = []
            for year, products in yearly_data.items():
                all_data.extend(products)
            
            if all_data:
                sheets_data["All Years"] = all_data
            
            # Xuất ra Excel với nhiều sheet
            export_util = ExportUtil()
            return await export_util._export_multiple_sheets_to_excel(
                sheets_data=sheets_data,
                filename_prefix=f"product_statistics_by_year_{year_start}_{year_end}_limit_{limit_per_year}"
            )
        except Exception as e:
            logger.error(f"Error exporting yearly statistics to Excel: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất thống kê theo năm ra Excel: {str(e)}")