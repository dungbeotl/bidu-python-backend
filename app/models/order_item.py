from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from beanie import Document
from beanie.odm.fields import PydanticObjectId



class OrderItem(Document):
    """
    Model OrderItem cho ứng dụng sử dụng Beanie ODM.

    Beanie tự động quản lý _id của MongoDB và chuyển đổi giữa
    Pydantic/MongoDB. Tất cả các phương thức CRUD được cung cấp sẵn.
    """

    # Reference đến Order
    order_id: Optional[PydanticObjectId] = Field(None, description="ID của đơn hàng")

    # Số lượng sản phẩm
    quantity: int = Field(default=1, description="Số lượng sản phẩm")

    # Thông tin variant của sản phẩm
    variant: Optional[Dict[str, Any]] = Field(
        None, description="Thông tin biến thể sản phẩm"
    )

    # Reference đến Product
    product_id: Optional[PydanticObjectId] = Field(None, description="ID của sản phẩm")

    # Thông tin sản phẩm được lưu trữ
    product: Optional[Dict[Any, Any]] = Field(None, description="Thông tin sản phẩm")

    # Danh sách hình ảnh
    images: List[Any] = Field(
        default_factory=list, description="Danh sách hình ảnh sản phẩm"
    )

    # Có áp dụng hệ thống khuyến mãi hay không
    has_promotion_system: bool = Field(
        default=False, description="Có áp dụng hệ thống khuyến mãi"
    )

    # Thông tin khuyến mãi
    promotion: Optional[Dict[Any, Any]] = Field(
        None, description="Thông tin khuyến mãi"
    )

    # Timestamps - Beanie sẽ tự động cập nhật những trường này
    created_at: Optional[datetime] = Field(None, description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật")

    class Settings:
        name = "orderitems"  # Tên collection trong MongoDB
        use_state_management = True  # Cho phép theo dõi thay đổi
        model_config = {
            "validate_assignment": True,
            "validate_default": True,
        }


OrderItemModel = OrderItem
