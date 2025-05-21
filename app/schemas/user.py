from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import UserModel, BodyMeasurement, NotificationSettings, NameOrganizer
from app.utils import MongoModel

class UserMinimalSchema(MongoModel):  # Kế thừa từ MongoModel để xử lý ObjectId
    """
    Schema tối thiểu cho API responses.

    Chỉ bao gồm các trường tối thiểu cần thiết.
    """

    userName: Optional[str] = None
    avatar: Optional[Any] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "_id": "60d1f0e7c80f760001f1c6e5",
                "userName": "johndoe",
                "avatar": "avatar_url.jpg",
            }
        }
    )


class UserSchema(UserModel):
    """
    Schema chuẩn cho API responses.

    Mở rộng từ UserModel và thêm các cấu hình đặc biệt cho API.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "_id": "60d1f0e7c80f760001f1c6e5",
                "email": "user@example.com",
                "userName": "johndoe",
                "gender": 1,
                "phoneNumber": "0987654321",
                "is_active": True,
                "is_superuser": False,
                "createdAt": "2023-09-01T12:00:00",
                "updatedAt": "2023-09-02T13:00:00",
            }
        },
        from_attributes=True,
        populate_by_name=True,
    )


class UserCreateSchema(BaseModel):
    """
    Schema cho việc tạo người dùng mới.

    Chỉ bao gồm các trường cần thiết cho việc tạo mới.
    """

    email: EmailStr
    userName: str
    password: str
    gender: Optional[int] = 3
    phoneNumber: Optional[str] = None
    birthday: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[Any] = None
    bodyMeasurement: Optional[BodyMeasurement] = None
    receiveNotifications: Optional[NotificationSettings] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "userName": "johndoe",
                "password": "StrongPass123",
                "gender": 1,
                "phoneNumber": "0987654321",
            }
        }
    )


class UserUpdateSchema(BaseModel):
    """
    Schema cho việc cập nhật thông tin người dùng.

    Tất cả các trường đều là tùy chọn.
    """

    email: Optional[EmailStr] = None
    userName: Optional[str] = None
    nameOrganizer: Optional[NameOrganizer] = None
    gender: Optional[int] = None
    phoneNumber: Optional[str] = None
    birthday: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[Any] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    bodyMeasurement: Optional[BodyMeasurement] = None
    receiveNotifications: Optional[NotificationSettings] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "gender": 1,
                "phoneNumber": "0987654321",
                "password": "NewStrongPass123",
            }
        }
    )
