from datetime import datetime
from typing import List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from app.utils import MongoModel


# Define enums for categorical fields
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECT = "reject"
    DRAFT = "draft"


# Define sub-schemas
class DescriptionImageSchema(BaseModel):
    url: Optional[str] = None
    width: int = 0
    height: int = 0


class CustomImageSchema(BaseModel):
    url: str = ""
    x_percent_offset: Optional[float] = Field(None, ge=0, le=100)
    y_percent_offset: Optional[float] = Field(None, ge=0, le=100)


class SoldInWeekSchema(BaseModel):
    startOfWeek: Optional[datetime] = None
    endOfWeek: Optional[datetime] = None
    sold: Optional[int] = None


# Base schema with common attributes
class ProductBase(BaseModel):
    """Base schema with common product attributes"""

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
    allow_to_sell: bool = True
    is_approved: ApprovalStatus = ApprovalStatus.PENDING
    is_pre_order: bool = True

    # Images
    images: List[str] = []
    authen_images: List[str] = []

    # Relations
    shop_id: Optional[str] = None
    category_id: Optional[str] = None

    # Other fields that might be useful for API responses
    sold: int = 0
    is_sold_out: bool = False
    is_guaranteed_item: bool = False
    is_genuine_item: bool = False
    sku: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


# Schema for product responses
class ProductSchema(ProductBase, MongoModel):
    """Schema for API responses"""

    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d1f0e7c80f760001f1c6e5",
                "name": "Product Name",
                "description": "Detailed product description",
                "short_description": "Short description",
                "before_sale_price": 100.0,
                "sale_price": 80.0,
                "quantity": 50,
                "is_approved": "approved",
                "images": ["image1.jpg", "image2.jpg"],
                "createdAt": "2023-01-01T00:00:00",
                "updatedAt": "2023-01-02T00:00:00",
                "sold": 10,
                "is_sold_out": False,
            }
        },
    )


# Schema for detailed product view
class ProductDetailSchema(ProductSchema):
    """Schema for detailed product information"""

    description_images: List[DescriptionImageSchema] = []
    custom_images: Optional[List[CustomImageSchema]] = None
    sold_in_week: Optional[SoldInWeekSchema] = None

    # Additional fields for detailed view
    shipping_information: str = ""
    delivery_instruction: str = ""
    delivery_information: str = ""
    allow_refund: bool = True
    duration_refund: int = 0

    list_category_id: List[Any] = []
    shorten_link: Optional[str] = None


# Schema for product listing (simplified)
class ProductListSchema(MongoModel):
    """Schema for product listing with minimal information"""

    name: str
    short_description: Optional[str] = None
    before_sale_price: float
    sale_price: Optional[float] = None
    is_sold_out: bool = False
    images: List[str] = []
    sold: int = 0
    is_guaranteed_item: bool = False
    is_genuine_item: bool = False

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
