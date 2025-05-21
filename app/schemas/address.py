from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict

from app.models import AddressModel, ExpectedDelivery, AddressType
from app.utils import MongoModel


# Model để tạo Address mới
class AddressCreate(BaseModel):
    name: str
    country: str = ""
    state: Optional[Dict[str, Any]] = None
    district: Optional[Dict[str, Any]] = None
    ward: Optional[Dict[str, Any]] = None
    street: Optional[str] = None
    phone: str
    accessible_id: Optional[str] = None
    accessible_type: str = "User"
    is_default: bool = False
    is_delivery_default: bool = False
    is_pick_address_default: bool = False
    is_return_address_default: bool = False
    expected_delivery: ExpectedDelivery = ExpectedDelivery.ANY_TIME
    address_type: AddressType = AddressType.HOME

    model_config = ConfigDict(use_enum_values=True)


# Model để cập nhật Address
class AddressUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    district: Optional[Dict[str, Any]] = None
    ward: Optional[Dict[str, Any]] = None
    street: Optional[str] = None
    phone: Optional[str] = None
    accessible_id: Optional[str] = None
    accessible_type: Optional[str] = None
    is_default: Optional[bool] = None
    is_delivery_default: Optional[bool] = None
    is_pick_address_default: Optional[bool] = None
    is_return_address_default: Optional[bool] = None
    expected_delivery: Optional[ExpectedDelivery] = None
    address_type: Optional[AddressType] = None

    model_config = ConfigDict(use_enum_values=True)


# Model cho response Address
class AddressOut(AddressModel, MongoModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d1f0e7c80f760001f1c6e5",
                "name": "Nguyễn Văn A",
                "country": "Việt Nam",
                "state": {"code": "01", "name": "Hà Nội"},
                "district": {"code": "001", "name": "Quận Ba Đình"},
                "ward": {"code": "00001", "name": "Phường Phúc Xá"},
                "street": "Số 1, Đường Hùng Vương",
                "phone": "0987654321",
                "accessible_id": "60d1f0e7c80f760001f1c6e6",
                "accessible_type": "User",
                "is_default": True,
                "is_delivery_default": True,
                "is_pick_address_default": False,
                "is_return_address_default": False,
                "expected_delivery": "any_time",
                "address_type": "home",
                "created_at": "2023-09-01T12:00:00",
                "updated_at": "2023-09-02T13:00:00",
            }
        },
    )
