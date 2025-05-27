from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from beanie import Document, Indexed
from beanie.odm.fields import PydanticObjectId


class Feedback(Document):
    """
    Model Feedback cho ứng dụng sử dụng Beanie ODM.

    Beanie tự động quản lý _id của MongoDB và chuyển đổi giữa
    Pydantic/MongoDB. Tất cả các phương thức CRUD được cung cấp sẵn.
    """

    # Nội dung phản hồi - bắt buộc
    content: str = Field(..., description="Nội dung phản hồi")

    # Số sao đánh giá - bắt buộc, từ 1-5
    vote_star: int = Field(..., ge=1, le=5, description="Số sao đánh giá (1-5)")

    # Danh sách media (hình ảnh, video)
    medias: List[str] = Field(default_factory=list, description="Danh sách media URLs")

    # Loại đối tượng feedback - bắt buộc
    target_type: str = Field(..., description="Loại đối tượng của phản hồi")

    # ID đối tượng feedback - bắt buộc
    target_id: Optional[PydanticObjectId] = Field(
        None, description="ID đối tượng của phản hồi"
    )

    # Trạng thái duyệt
    is_approved: bool = Field(default=True, description="Phản hồi đã được duyệt")

    # Hiển thị công khai
    is_public: bool = Field(default=True, description="Hiển thị công khai")

    # Hiển thị thông tin vóc dáng
    is_show_body_shape: bool = Field(
        default=True, description="Hiển thị thông tin vóc dáng"
    )

    # References đến các entities khác
    user_id: Optional[PydanticObjectId] = Field(None, description="ID người dùng")

    shop_id: Optional[PydanticObjectId] = Field(None, description="ID cửa hàng")

    order_id: Optional[PydanticObjectId] = Field(None, description="ID đơn hàng")

    order_item_id: Optional[PydanticObjectId] = Field(
        None, description="ID sản phẩm trong đơn"
    )

    # Danh sách user đã like feedback này
    user_liked: List[Any] = Field(
        default_factory=list, description="Danh sách user đã like"
    )

    # Trạng thái đã chỉnh sửa
    is_edited: bool = Field(default=False, description="Feedback đã được chỉnh sửa")

    # Timestamps - Beanie sẽ tự động cập nhật những trường này
    created_at: Optional[datetime] = Field(None, description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật")

    class Settings:
        name = "feedbacks"  # Tên collection trong MongoDB
        use_state_management = True  # Cho phép theo dõi thay đổi

FeedbackModel = Feedback
