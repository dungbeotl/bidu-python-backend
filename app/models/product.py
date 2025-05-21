from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from beanie import Document

# Define enums for categorical fields
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECT = "reject"
    DRAFT = "draft"


# Define sub-models
class DescriptionImage(BaseModel):
    url: Optional[str] = None
    width: int = 0
    height: int = 0


class CustomImage(BaseModel):
    url: str = ""
    x_percent_offset: Optional[float] = Field(None, ge=0, le=100)
    y_percent_offset: Optional[float] = Field(None, ge=0, le=100)


class SoldInWeek(BaseModel):
    startOfWeek: Optional[datetime] = None
    endOfWeek: Optional[datetime] = None
    sold: Optional[int] = None


# Model for database using Beanie
class Product(Document):
    """Model that represents a product in the database using Beanie ODM"""

    # Basic information
    name: str
    description: str
    short_description: Optional[str] = None
    friendly_url: Optional[str] = None

    # Dimensions
    weight: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    length: Optional[float] = None

    # Pricing
    before_sale_price: float
    sale_price: Optional[float] = None
    quantity: int = 0

    # Status fields
    deleted_at: Optional[datetime] = None
    allow_to_sell: bool = True
    is_approved: str = ApprovalStatus.PENDING
    is_pre_order: bool = True

    # Images
    images: List[str] = []
    authen_images: List[str] = []
    description_images: List[DescriptionImage] = []
    custom_images: Optional[List[CustomImage]] = None

    # Relations
    shop_id: Optional[str] = None
    category_id: Optional[str] = None
    list_category_id: List[Any] = []

    # Sales information
    limit_sale_price_order: int = 0
    sale_price_order_available: int = 0
    sold: int = 0
    sold_in_week: Optional[SoldInWeek] = None

    # Shipping and delivery
    shipping_information: str = ""
    delivery_instruction: str = ""
    exchange_information: str = ""  # Not used anymore but kept
    delivery_information: str = ""

    # Refund policy
    allow_refund: bool = True
    duration_refund: int = 0

    # Marketing
    shorten_link: Optional[str] = None
    popular_mark: int = 0
    body_shape_mark: Optional[Dict[str, Any]] = None
    is_suggested: Union[bool, Dict[str, Any]] = False

    # Product quality
    is_guaranteed_item: bool = False  # Hàng được đảm bảo
    is_genuine_item: bool = False  # Hàng chính hãng

    # Display settings
    top_photo_display_full_mode: bool = False

    # Price update tracking
    update_price_remaining: int = 3
    next_date_update_price: Optional[datetime] = None
    price_updated_dates: List[Any] = []

    # Stock status
    is_sold_out: bool = False

    # SKU
    sku: Optional[str] = None

    # Timestamp fields không cần khai báo, sẽ được Beanie tự động cập nhật
    createdAt: datetime
    updatedAt: datetime

    class Settings:
        name = "products"  # Tên collection trong MongoDB
        use_state_management = True

# Để tương thích ngược với mã hiện có
ProductModel = Product
