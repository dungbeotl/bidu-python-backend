from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from beanie import Document
from beanie.odm.fields import PydanticObjectId



class Order(Document):
    """
    Model Order cho ứng dụng sử dụng Beanie ODM.

    Beanie tự động quản lý _id của MongoDB và chuyển đổi giữa
    Pydantic/MongoDB. Tất cả các phương thức CRUD được cung cấp sẵn.
    """
    order_number: str = Field(description="Số đơn hàng")
    
    total_price: float = Field(description="Tổng giá trị đơn hàng")
    
    total_value_items: float = Field(description="Tổng giá trị sản phẩm")
    
    shipping_discount: float = Field(description="Tổng giảm giá vận chuyển")
    
    voucher_discount: float = Field(description="Tổng giảm giá voucher")
    
    
    shipping_fee: float = Field(description="Tổng phí vận chuyển")
    
    group_order_id: float = Field(description="ID nhóm đơn hàng")
    
    payment_status: str = Field(description="Trạng thái thanh toán")
    
    shipping_status: str = Field(description="Trạng thái vận chuyển")
    
    payment_method_id: str = Field(description="ID phương thức thanh toán")
    
    user_id: str = Field(description="ID người dùng")
    
    shop_id: str = Field(description="ID shop")
    
    # Timestamps - Beanie sẽ tự động cập nhật những trường này
    created_at: Optional[datetime] = Field(None, description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật")
    
    class Settings:
        name = "orders"  # Tên collection trong MongoDB
        use_state_management = True  # Cho phép theo dõi thay đổi
        model_config = {
            "validate_assignment": True,
            "validate_default": True,
        }
    
OrderModel = Order