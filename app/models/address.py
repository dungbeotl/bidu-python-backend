from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field
from beanie import Document


# Enums cho các trường giới hạn giá trị
class ExpectedDelivery(str, Enum):
    ANY_TIME = "any_time"
    WORK_TIME = "work_time"


class AddressType(str, Enum):
    HOME = "home"
    COMPANY = "company"


# Model cho location (state, district, ward)
class LocationModel(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

    class Config:
        extra = "allow"  # Cho phép các trường khác nếu có


# Beanie Document cho Address
class Address(Document):
    name: str = Field(..., description="Tên người nhận")
    country: str = Field("", description="Quốc gia")
    state: Optional[Dict[str, Any]] = Field(None, description="Tỉnh/Thành phố")
    district: Optional[Dict[str, Any]] = Field(None, description="Quận/Huyện")
    ward: Optional[Dict[str, Any]] = Field(None, description="Phường/Xã")
    street: Optional[str] = Field(None, description="Đường/Phố")
    phone: str = Field(..., description="Số điện thoại")
    accessible_id: Optional[str] = Field(None, description="ID của đối tượng liên kết")
    accessible_type: str = Field("User", description="Loại đối tượng liên kết")
    is_default: bool = Field(False, description="Địa chỉ mặc định")
    is_delivery_default: bool = Field(False, description="Địa chỉ giao hàng mặc định")
    is_pick_address_default: bool = Field(
        False, description="Địa chỉ lấy hàng mặc định"
    )
    is_return_address_default: bool = Field(
        False, description="Địa chỉ hoàn hàng mặc định"
    )
    expected_delivery: ExpectedDelivery = Field(
        ExpectedDelivery.ANY_TIME, description="Thời gian giao hàng dự kiến"
    )
    address_type: AddressType = Field(AddressType.HOME, description="Loại địa chỉ")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian tạo")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Thời gian cập nhật"
    )

    class Settings:
        name = "addresses"  # Tên collection trong MongoDB
        use_state_management = True

# Để tương thích ngược với mã hiện có
AddressModel = Address
