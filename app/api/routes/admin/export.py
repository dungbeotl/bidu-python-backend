from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_superuser
from app.services.user import UserService
from app.services.product import ProductService
from bson import ObjectId

router = APIRouter()


@router.get(
    "/personalize/users",
    summary="Xuất dữ liệu người dùng cho AWS Personalize",
    description="""
    Xuất dữ liệu người dùng đã được định dạng cho AWS Personalize.
    
    Chuyển đổi dữ liệu:
    - GENDER: male, female, other, null
    - AGE_GROUP: 18-24, 25-34, 35-44, 45+, null
    - MEMBERSHIP_DURATION: 0-6_months, 6-12_months, 1-2_years, 2+_years, null
    - LOCATION: Thành phố của người dùng, lấy từ địa chỉ mặc định
    
    Định dạng xuất:
    - json: JSONL format (mỗi record là 1 dòng)
    - csv: CSV format
    """,
    response_class=StreamingResponse,
)
async def export_users_for_personalize(
    format: str = Query("json", description="Định dạng xuất (json, csv)"),
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
        format=format, limit=limit, filter_dict=filter_dict
    )


@router.get(
    "/personalize/users/preview",
    response_model=List[Dict[str, Any]],
    summary="Xem trước dữ liệu cho AWS Personalize",
    description="Xem trước dữ liệu người dùng đã được định dạng cho AWS Personalize.",
)
async def preview_users_for_personalize(
    limit: int = Query(10, ge=1, le=100, description="Số lượng người dùng tối đa"),
    is_active: Optional[bool] = Query(
        None, description="Lọc theo trạng thái kích hoạt"
    ),
):
    """
    Xem trước dữ liệu người dùng đã được định dạng cho AWS Personalize.
    Chỉ superuser mới có quyền truy cập.
    """
    # Tạo filter dict
    filter_dict = {}
    if is_active is not None:
        filter_dict["is_active"] = is_active

    # Lấy dữ liệu từ repository
    user_service = UserService()
    users_data = await user_service.repository.get_users_for_personalize(
        limit=limit, filter_dict=filter_dict
    )

    return users_data


@router.get(
    "/personalize/products",
    summary="Xuất dữ liệu sản phẩm cho AWS Personalize",
    description="""
    Xuất dữ liệu sản phẩm đã được định dạng cho AWS Personalize.
    
    Chuyển đổi dữ liệu:
    - ITEM_ID: ID của sản phẩm
    - ITEM_STATUS: Trạng thái sản phẩm (ACTIVE, PENDING, DRAFT, DELETED)
    
    Định dạng xuất:
    - json: JSONL format (mỗi record là 1 dòng)
    - csv: CSV format
    """,
    response_class=StreamingResponse,
)
async def export_products_for_personalize(
    format: str = Query("json", description="Định dạng xuất (json, csv)"),
    limit: Optional[int] = Query(None, description="Số lượng sản phẩm tối đa"),
    is_approved: Optional[str] = Query(
        None, description="Lọc theo trạng thái phê duyệt (approved, pending, draft)"
    ),
    include_deleted: bool = Query(True, description="Bao gồm cả sản phẩm đã xóa"),
    include_categories: bool = Query(False, description="Bao gồm thông tin danh mục"),
    include_detail_info: bool = Query(False, description="Bao gồm thông tin chi tiết"),
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
    return await product_service.export_products_for_personalize(
        format=format,
        limit=limit,
        filter_dict=filter_dict,
        include_categories=include_categories,
        include_detail_info=include_detail_info,
    )


@router.get(
    "/personalize/products/preview",
    response_model=List[Dict[str, Any]],
    summary="Xem trước dữ liệu sản phẩm cho AWS Personalize",
    description="Xem trước dữ liệu sản phẩm đã được định dạng cho AWS Personalize.",
)
async def preview_products_for_personalize(
    limit: int = Query(10, ge=1, le=10000, description="Số lượng sản phẩm tối đa"),
    is_approved: Optional[str] = Query(
        None, description="Lọc theo trạng thái phê duyệt (approved, pending, draft)"
    ),
    include_deleted: bool = Query(False, description="Bao gồm cả sản phẩm đã xóa"),
    include_categories: bool = Query(False, description="Bao gồm thông tin danh mục"),
    include_detail_info: bool = Query(False, description="Bao gồm thông tin chi tiết"),
    # current_user: Dict = Depends(get_current_superuser)
):
    """
    Xem trước dữ liệu sản phẩm đã được định dạng cho AWS Personalize.
    Chỉ superuser mới có quyền truy cập.
    """
    # Tạo filter dict
    filter_dict = {"_id": {"$eq": ObjectId("617bde26f8aa33001191691e")}}

    # Lọc theo trạng thái phê duyệt
    if is_approved:
        filter_dict["is_approved"] = is_approved

    # Loại bỏ sản phẩm đã xóa nếu không bao gồm
    if not include_deleted:
        filter_dict["deleted_at"] = None

    # Lấy dữ liệu từ repository
    product_service = ProductService()
    products_raw = await product_service.repository.get_products_for_personalize(
        limit=limit,
        filter_dict=filter_dict,
        include_categories=include_categories,
        include_detail_info=include_detail_info,
    )

    products_data = await product_service._process_products_for_personalize(products_raw)
    return products_data
