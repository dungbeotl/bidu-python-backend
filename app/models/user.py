from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from beanie import Document


class MemberType(str, Enum):
    WHITE = "WHITE"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"

class BodyMeasurement(BaseModel):
    """Schema cho kích thước cơ thể."""
    height: Optional[float] = None
    weight: Optional[float] = None
    bustSize: Optional[float] = None
    waistSize: Optional[float] = None
    highHipSize: Optional[float] = None
    hipSize: Optional[float] = None

class TokenInfo(BaseModel):
    """Schema cho thông tin token thanh toán."""
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_icon: Optional[str] = None
    card_type: Optional[str] = None
    token: Optional[str] = None
    payment_name: Optional[str] = None
    card_number: Optional[str] = None
    last_selected: bool = False
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

class OnepayCardTokenInfo(TokenInfo):
    """Schema cho thông tin token thẻ Onepay."""
    card_uid: Optional[str] = None
    token_exp: Optional[str] = None
    merchant: Optional[str] = None

class FavoriteBlog(BaseModel):
    """Schema cho blog yêu thích."""
    blog_id: str
    created_at: datetime

class SizeInfo(BaseModel):
    """Schema cho thông tin kích cỡ."""
    name: str
    min: int = 0
    max: int = 0
    unit: str

class TypeSize(BaseModel):
    """Schema cho loại kích cỡ."""
    type_size: str
    size_infos: List[SizeInfo]

class FashionType(BaseModel):
    """Schema cho loại thời trang."""
    fashion_type: int
    data: List[TypeSize]

class ShapeHistory(BaseModel):
    """Schema cho lịch sử hình dáng."""
    category_id: Optional[str] = None
    weight: float = 0
    height: float = 0
    width: float = 0
    length: float = 0
    time: datetime

class NotificationSettings(BaseModel):
    """Schema cho cài đặt thông báo."""
    like: bool = True
    comment: bool = True
    follow: bool = True
    tag: bool = True
    other: bool = True

class EmailVerification(BaseModel):
    """Schema cho xác thực email."""
    verified: bool = False
    code: Optional[int] = None
    expire: Optional[datetime] = None

class PhoneVerification(BaseModel):
    """Schema cho xác thực số điện thoại."""
    verified: bool = False
    code: Optional[int] = None
    expire: Optional[datetime] = None

class NameOrganizer(BaseModel):
    """Schema cho tên."""
    userName: Optional[str] = None # Tên người dùng
    unsigneduserName: Optional[str] = None # Tên người dùng không dấu

class SocialAccount(BaseModel):
    """Schema cho tài khoản mạng xã hội."""
    id: str  # ID của tài khoản mạng xã hội, không phải là MongoDB ObjectId
    socialName: str

class User(Document):
    """
    Model user tổng quát cho ứng dụng sử dụng Beanie ODM.
    
    Beanie tự động quản lý _id của MongoDB và chuyển đổi giữa
    Pydantic/MongoDB. Tất cả các phương thức CRUD được cung cấp sẵn.
    """
    # Thông tin cơ bản
    email: Optional[EmailStr] = None
    userName: Optional[str] = None
    nameOrganizer: Optional[NameOrganizer] = None
    gender: int = 3
    phoneNumber: Optional[str] = None
    birthday: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[Any] = None
    
    # Trạng thái người dùng
    is_active: bool = True
    is_superuser: bool = False
    isVerified: bool = False
    isInterestShowed: bool = False
    verificationType: int = 0
    customVerify: Optional[str] = None
    is_newbie: bool = True
    is_guest: Optional[bool] = None
    
    # Thông tin xác thực
    password: Optional[str] = None  # Trường cho validator, không lưu vào DB
    hashed_password: Optional[str] = None
    email_verify: EmailVerification = EmailVerification()
    phone_verify: PhoneVerification = PhoneVerification()
    
    # Thiết lập tùy chọn
    referral_code: Optional[str] = None
    bodyMeasurement: Optional[BodyMeasurement] = None
    receiveNotifications: NotificationSettings = NotificationSettings()
    shorten_link: Optional[str] = None
    
    # Phân quyền và vai trò
    type_role: str = "USER"
    member_type: MemberType = MemberType.WHITE
    group_roles: List[Any] = []
    
    # Thông tin thêm
    is_seller_signup: bool = False
    custom_title: Optional[str] = None
    custom_titles: List[str] = []
    
    # Thống kê
    followCount: int = 0
    followingCount: int = 1
    totalPosts: int = 0
    
    # Dữ liệu liên kết
    favorite_products: List[Any] = []
    saved_vouchers: List[Any] = []
    detail_size_history: List[FashionType] = []
    shape_history: List[ShapeHistory] = []
    category_info_history: Optional[Dict[str, Any]] = None
    card_token_infos: List[TokenInfo] = []
    favorite_blogs: List[FavoriteBlog] = []
    onepay_card_token_infos: List[OnepayCardTokenInfo] = []
    socialAccount: Optional[Dict[str, Any]] = None
    
    # Timestamp - Beanie sẽ tự động cập nhật những trường này
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    lastActivityAt: Optional[datetime] = None
    
    class Settings:
        name = "users"  # Tên collection trong MongoDB
        use_state_management = True  # Cho phép theo dõi thay đổi
        model_config = {
            "validate_assignment": True,
            "validate_default": True,
        }

    @field_validator('password')
    def password_must_be_strong(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        if not any(c.isupper() for c in v):
            raise ValueError('Mật khẩu phải có ít nhất một chữ hoa')
        if not any(c.islower() for c in v):
            raise ValueError('Mật khẩu phải có ít nhất một chữ thường')
        if not any(c.isdigit() for c in v):
            raise ValueError('Mật khẩu phải có ít nhất một chữ số')
        return v

# Giữ UserModel phù hợp ngược để tương thích với code hiện có
UserModel = User