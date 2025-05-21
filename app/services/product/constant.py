from dataclasses import dataclass


# Constants
class ProductStatus:
    PENDING = "PENDING"
    DELETED = "DELETED"
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"


class ApprovalStatus:
    APPROVED = "approved"
    DRAFT = "draft"


class CategoryNames:
    GENDER = "Gender"
    BRAND = "Brand"
    ORIGIN = "Origin"
    STYLE = "Style"
    SEASON = "Season"


DEFAULT_VALUE = "UNKNOWN"
MAX_CATEGORY_LEVELS = 4


@dataclass
class ProcessedProductDetails:
    """Dataclass để lưu thông tin chi tiết sản phẩm đã xử lý"""

    gender: str = DEFAULT_VALUE
    brand: str = DEFAULT_VALUE
    origin: str = DEFAULT_VALUE
    style: str = DEFAULT_VALUE
    seasons: str = DEFAULT_VALUE
