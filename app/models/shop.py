from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from beanie import Document, Indexed
from beanie.odm.fields import PydanticObjectId


class ShopIndustryType(str, Enum):
    """Enum cho loại ngành của shop."""

    COSMETICS = "COSMETICS"
    FASHIONS = "FASHIONS"
    OTHER = "OTHER"


class Shop(Document):
    """
    Model Shop cho ứng dụng sử dụng Beanie ODM.

    Beanie tự động quản lý _id của MongoDB và chuyển đổi giữa
    Pydantic/MongoDB. Tất cả các phương thức CRUD được cung cấp sẵn.
    """

    # Thông tin cơ bản
    name: Optional[str] = Field(None, description="Tên shop")
    description: Optional[str] = Field(None, description="Mô tả shop")

    # Loại shop và trạng thái
    shop_type: int = Field(default=0, description="Loại shop")
    pause_mode: bool = Field(default=False, description="Chế độ tạm dừng")

    # Reference đến User - có index
    user_id: Optional[PydanticObjectId] = Field(
        None, description="ID người dùng sở hữu shop"
    )

    # Thông tin địa lý
    country: Optional[str] = Field(None, description="Quốc gia")

    # Trạng thái duyệt
    is_approved: bool = Field(default=False, description="Shop đã được duyệt")

    # Ranking
    ranking_today: int = Field(default=99999, description="Xếp hạng hôm nay")
    ranking_yesterday: int = Field(default=99999, description="Xếp hạng hôm qua")

    # Rating và đánh giá
    avg_rating: float = Field(
        default=5.0, ge=0.0, le=5.0, description="Đánh giá trung bình"
    )

    # Link và thông tin khác
    shorten_link: Optional[str] = Field(None, description="Link rút gọn")
    biggest_price: float = Field(default=0.0, ge=0, description="Giá cao nhất")

    # Loại ngành nghề
    shop_industry_type: ShopIndustryType = Field(
        default=ShopIndustryType.OTHER, description="Loại ngành nghề của shop"
    )

    # Thống kê
    total_revenue: float = Field(default=0.0, ge=0, description="Tổng doanh thu")
    total_active_product: int = Field(
        default=0, ge=0, description="Tổng sản phẩm đang hoạt động"
    )

    # Thời gian duyệt/từ chối
    approved_by_admin_at: Optional[datetime] = Field(
        None, description="Thời gian được admin duyệt"
    )
    reject_by_admin_at: Optional[datetime] = Field(
        None, description="Thời gian bị admin từ chối"
    )

    # Timestamps - Beanie sẽ tự động cập nhật những trường này
    created_at: Optional[datetime] = Field(None, description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật")

    # Cấu hình Pydantic
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,  # Cho phép sử dụng enum values
    )

    class Settings:
        name = "shops"  # Tên collection trong MongoDB
        use_state_management = True


ShopModel = Shop
