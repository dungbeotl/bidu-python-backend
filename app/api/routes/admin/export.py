from typing import Dict, List, Any, Optional
import logging
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_superuser
from app.services import UserService, ProductService, InteractionService, ShopService
from app.services.order import OrderService
from bson import ObjectId

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/personalize/users",
    summary="Xuất dữ liệu người dùng cho AWS Personalize",
    description="""
    Xuất dữ liệu người dùng đã được định dạng cho AWS Personalize.
    
    Format Custom (personalize_format=custom):
    - USER_ID: ID của người dùng
    - GENDER: male, female, unisex
    - AGE_GROUP: 18-24, 25-34, 35-44, 45+, unknown
    - MEMBERSHIP_DURATION: 0-6_months, 6-12_months, 1-2_years, 2+_years, unknown  
    - LOCATION: Thành phố của người dùng, lấy từ địa chỉ mặc định
    
    Format E-commerce (personalize_format=ecommerce):
    - USER_ID: ID của người dùng
    - GENDER: male, female, unisex
    
    Định dạng xuất:
    - json: JSONL format (mỗi record là 1 dòng)
    - csv: CSV format
    """,
    response_class=StreamingResponse,
)
async def export_users_for_personalize(
    format: str = Query("csv", description="Định dạng xuất (json, csv)"),
    personalize_format: str = Query(
        "ecommerce", description="Format cho Personalize (custom, ecommerce)"
    ),
    limit: Optional[int] = Query(None, description="Số lượng người dùng tối đa"),
    is_active: Optional[bool] = Query(
        None, description="Lọc theo trạng thái kích hoạt"
    ),
):
    """
    Xuất dữ liệu người dùng đã được định dạng cho AWS Personalize.
    Chỉ superuser mới có quyền truy cập.
    """
    # Tạo filter dict
    filter_dict = {}
    if is_active is not None:
        filter_dict["is_active"] = is_active

    # Gọi service
    user_service = UserService()
    return await user_service.export_users_for_personalize(
        format=format, 
        limit=limit, 
        filter_dict=filter_dict,
        personalize_format=personalize_format
    )


@router.get(
    "/personalize/products",
    summary="Xuất dữ liệu sản phẩm cho AWS Personalize",
    description="""
    Xuất dữ liệu sản phẩm đã được định dạng cho AWS Personalize.
    
    Format Custom (personalize_format=custom):
    - ITEM_ID: ID của sản phẩm
    - ITEM_STATUS: Trạng thái sản phẩm (ACTIVE, PENDING, DRAFT, DELETED)
    - PRICE_MIN, PRICE_MAX: Giá min và max
    - CATEGORY_L1,L2,L3,L4: Tên category các level
    - GENDER, ORIGIN, STYLE, SEASONS: Thông tin chi tiết
    - TIMESTAMP: Thời gian tạo
    
    Format E-commerce (personalize_format=ecommerce):
    - ITEM_ID: ID của sản phẩm
    - PRICE: Giá min của sản phẩm
    - CATEGORY_L1,L2,L3: Tên category các level
    - GENDER: male, female, unisex, null
    - CREATION_TIMESTAMP: Thời gian tạo
    
    Định dạng xuất:
    - json: JSONL format (mỗi record là 1 dòng)
    - csv: CSV format
    """,
    response_class=StreamingResponse,
)
async def export_products_for_personalize(
    format: str = Query("csv", description="Định dạng xuất (json, csv)"),
    personalize_format: str = Query(
        "ecommerce", description="Format cho Personalize (custom, ecommerce)"
    ),
    limit: Optional[int] = Query(None, description="Số lượng sản phẩm tối đa"),
    is_approved: Optional[str] = Query(
        None, description="Lọc theo trạng thái phê duyệt (approved, pending, draft)"
    ),
    include_deleted: bool = Query(True, description="Bao gồm cả sản phẩm đã xóa"),
    include_categories: bool = Query(True, description="Bao gồm thông tin danh mục"),
    include_detail_info: bool = Query(True, description="Bao gồm thông tin chi tiết"),
    include_variant: bool = Query(True, description="Bao gồm thông tin variant"),
    # current_user: Dict = Depends(get_current_superuser)
):
    """
    Xuất dữ liệu sản phẩm đã được định dạng cho AWS Personalize.
    Chỉ superuser mới có quyền truy cập.
    """
    # Tạo filter dict
    filter_dict = {}

    # Lọc theo trạng thái phê duyệt
    if is_approved:
        filter_dict["is_approved"] = is_approved

    # Loại bỏ sản phẩm đã xóa nếu không bao gồm
    if not include_deleted:
        filter_dict["deleted_at"] = None

    # Gọi service
    product_service = ProductService()

    # Chọn function dựa trên personalize_format
    return await product_service.export_products_for_personalize(
        format=format,
        limit=limit,
        filter_dict=filter_dict,
        include_categories=include_categories,
        include_detail_info=include_detail_info,
        include_variant=include_variant,
        personalize_format=personalize_format,
    )


@router.get(
    "/personalize/interactions/export",
    response_class=StreamingResponse,
    summary="Xuất dữ liệu Tương tác (Interactions) cho AWS Personalize",
    description="""
    Xuất dữ liệu tương tác đã được định dạng cho AWS Personalize.
    
    Format Custom (personalize_format=custom):
    - USER_ID, ITEM_ID, EVENT_TYPE, TIMESTAMP
    - SHOP_ID, EVENT_VALUE, ORDER_VALUE, BASKET_SIZE
    - PAYMENT_METHOD, DELIVERY_LOCATION
    
    Format E-commerce (personalize_format=ecommerce):
    - USER_ID, ITEM_ID, TIMESTAMP, EVENT_TYPE, EVENT_VALUE
    
    Định dạng xuất:
    - json: JSONL format (mỗi record là 1 dòng)
    - csv: CSV format
    """,
)
async def export_interactions_for_personalize(
    format: str = Query("csv", description="Định dạng xuất (json, csv)"),
    personalize_format: str = Query(
        "ecommerce", description="Format cho Personalize (custom, ecommerce)"
    ),
    limit: int = Query(10, ge=1, le=10000, description="Số lượng tương tác tối đa"),
    # current_user: Dict = Depends(get_current_superuser)
):
    """
    Xuất dữ liệu tương tác đã được định dạng cho AWS Personalize.
    Chỉ superuser mới có quyền truy cập.
    """
    # Lấy dữ liệu từ repository
    interaction_service = InteractionService()
    return await interaction_service.export_interactions_for_personalize(
        format=format, personalize_format=personalize_format
    )


# **************************************************
# Statistics Product/Orders Routes
# **************************************************
@router.get(
    "/products/statistics/excel",
    summary="Xuất thống kê sản phẩm bán chạy ra file Excel",
    description="""
    Xuất thống kê top 50 sản phẩm có lượt bán cao nhất ra file Excel.
    
    File Excel sẽ chứa các thông tin:
    - Product ID: ID của sản phẩm
    - Product Name: Tên sản phẩm 
    - Product Shorten Link: Link rút gọn (bidu.vn + shorten_link)
    - Product Sold: Số lượng đã bán
    - Product Price: Giá sản phẩm (format: min-max)
    - Product Created At: Ngày tạo (format: dd/mm/yyyy)
    - Product Deleted At: Trạng thái xóa ("Deleted" hoặc "")
    - Product Is Approved: Trạng thái phê duyệt (Approved/Draft/Pending)
    - Product Shop Name: Tên shop
    - Product Shop Shorten Link: Link shop (bidu.vn + shop_shorten_link)
    """,
    response_class=StreamingResponse,
)
async def export_product_statistics_excel(
    # current_user: Dict = Depends(get_current_superuser)
):
    """
    Xuất thống kê sản phẩm bán chạy ra file Excel.
    Chỉ superuser mới có quyền truy cập.
    """
    product_service = ProductService()
    return await product_service.export_statistics_to_excel()


@router.get(
    "/products/statistics-by-year/excel",
    summary="Xuất thống kê sản phẩm bán chạy theo năm ra file Excel với nhiều sheet",
    description="""
    Xuất thống kê top sản phẩm có lượt bán cao nhất theo từng năm ra file Excel (tối đa 1000 sản phẩm/năm).
    Bao gồm đầy đủ thông tin sản phẩm, shop và trạng thái.
    
    File Excel sẽ chứa nhiều sheet:
    - "Year 2023": Dữ liệu sản phẩm bán chạy năm 2023
    - "Year 2024": Dữ liệu sản phẩm bán chạy năm 2024  
    - "Year 2025": Dữ liệu sản phẩm bán chạy năm 2025
    - "All Years": Tổng hợp tất cả các năm
    
    Mỗi sheet chứa các thông tin:
    - Year: Năm thống kê
    - Product ID: ID của sản phẩm
    - Product Name: Tên sản phẩm 
    - Product Shorten Link: Link rút gọn (bidu.vn + shorten_link)
    - Product Sold: Số lượng đã bán trong năm (từ order_items)
    - Product Price: Giá sản phẩm (format: min-max)
    - Product Created At: Ngày tạo (format: dd/mm/yyyy)
    - Product Deleted At: Trạng thái xóa ("Deleted" hoặc "")
    - Product Is Approved: Trạng thái phê duyệt (Approved/Draft/Pending/Rejected)
    - Product Shop Name: Tên shop
    - Product Shop Shorten Link: Link shop (bidu.vn + shop_shorten_link)
    """,
    response_class=StreamingResponse,
)
async def export_product_statistics_by_year_to_excel(
    year_start: int = Query(2023, description="Năm bắt đầu"),
    year_end: int = Query(2025, description="Năm kết thúc"),
    limit_per_year: int = Query(
        50, ge=1, le=1000, description="Số lượng sản phẩm tối đa mỗi năm"
    ),
    # current_user: Dict = Depends(get_current_superuser)
):
    """
    Xuất thống kê sản phẩm bán chạy theo từng năm với thông tin chi tiết ra Excel.
    Chỉ superuser mới có quyền truy cập.
    """
    order_service = OrderService()
    return await order_service.export_statistics_with_product_info_to_excel(
        year_start=year_start, year_end=year_end, limit_per_year=limit_per_year
    )

@router.post(
    "/shops/by-ids",
    summary="Lấy thông tin shop theo danh sách IDs",
    description="""
    Lấy thông tin shop theo danh sách IDs.
    Trả về dữ liệu gồm:
    - _id: ID của shop
    - updatedAt: Thời gian cập nhật cuối cùng
    """,
)
async def get_shop_by_ids(
    shop_ids: List[str] = Query(..., description="Danh sách shop IDs")
):
    """
    Lấy thông tin shop theo danh sách IDs.
    Chỉ superuser mới có quyền truy cập.
    """
    try:
        shop_service = ShopService()
        shops = await shop_service.get_shop_by_ids(shop_ids)
        
        return {
            "success": True,
            "message": f"Lấy thông tin {len(shops)} shop thành công",
            "data": shops,
            "total": len(shops)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin shop: {str(e)}"
        )