from datetime import datetime
from typing import Optional, List, Any, Union
from beanie import Document, Link
from pydantic import Field, ConfigDict
from bson import ObjectId


class ECategory(Document):
    """Model đại diện cho danh mục sản phẩm (ECategory) sử dụng Beanie ODM"""

    # Thông tin cơ bản
    name: str = Field(..., description="Tên danh mục")
    description: Optional[str] = None
    permalink: Optional[str] = None
    priority: Optional[int] = None
    is_active: bool = True
    avatar: Optional[str] = None
    pdfAvatar: Optional[str] = None

    # Quan hệ với danh mục cha (self-reference)
    # ObjectId hoặc str đều được chấp nhận cho parent_id
    parent_id: Optional[Union[str, ObjectId]] = Field(None, description="ID của danh mục cha, null nếu là cấp 0")

    # Các thông tin bổ sung
    type: Optional[str] = None
    industry: Optional[str] = None
    version: Optional[str] = None
    is_show_home: Optional[bool] = None

    # Timestamp fields
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    # Cấu hình Pydantic để cho phép kiểu dữ liệu tùy ý như ObjectId
    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "ecategories"  # Tên collection trong MongoDB
        use_state_management = True
        

ECategoryModel = ECategory
