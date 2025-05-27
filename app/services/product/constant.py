from dataclasses import dataclass
from app.constants import unknown

# Constants
class ProductStatus:
    PENDING = "pending"
    DELETED = "deleted"
    ACTIVE = "active"
    DRAFT = "draft"
    UNAVAILABLE = "unavailable"


class ApprovalStatus:
    APPROVED = "approved"
    DRAFT = "draft"


class CategoryNames:
    GENDER = "Gender"
    BRAND = "Brand"
    ORIGIN = "Origin"
    STYLE = "Style"
    SEASON = "Season"


MAX_CATEGORY_LEVELS = 4


@dataclass
class ProcessedProductDetails:
    """Dataclass để lưu thông tin chi tiết sản phẩm đã xử lý"""

    gender: str = unknown
    brand: str = unknown
    origin: str = unknown
    style: str = unknown
    seasons: str = unknown
