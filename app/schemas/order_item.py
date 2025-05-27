from pydantic import ConfigDict

from app.models import OrderItemModel


class OrderItemSchema(OrderItemModel):
    """
    Schema chuẩn cho API responses.

    Mở rộng từ OrderItemModel và thêm các cấu hình đặc biệt cho API.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "_id": "60d1f0e7c80f760001f1c6e5",
                "order_id": "60d1f0e7c80f760001f1c6e6",
                "product_id": "60d1f0e7c80f760001f1c6e7",
                "quantity": 2,
                "variant": {"size": "M", "color": "red"},
                "product": {"name": "Áo thun nam", "price": 299000},
                "images": ["image1.jpg", "image2.jpg"],
                "has_promotion_system": True,
                "promotion": {"discount_percent": 10, "promotion_code": "SALE10"},
                "created_at": "2023-09-01T12:00:00",
                "updated_at": "2023-09-02T13:00:00",
            }
        },
        from_attributes=True,
        populate_by_name=True,
    )
