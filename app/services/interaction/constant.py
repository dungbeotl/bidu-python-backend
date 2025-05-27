import pytz
from enum import Enum

# Constants
TZ_ASIA_HCM = pytz.timezone("Asia/Ho_Chi_Minh")


class TrackingType(Enum):
    """Tracking action types."""

    VIEW_PRODUCT = "view_product"
    ADD_PRODUCT_TO_CART = "add_cart"
    BUY_PRODUCT = "buy_product"
    ADD_PRODUCT_TO_FAVORITE = "add_product_to_favorite"
    REVIEW = "review"


class TableName:
    """Table/Collection names."""

    TRACKING_ACTIVITIES = "trackingactivities_production"
