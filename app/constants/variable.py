from enum import Enum

unknown = "unknown"

# Payment method id
class PaymentMethodId(Enum):
    CASH_ID = "6080f987ca33c1913de1be38"  # CASH
    VNPAY_ID = "6080f24dca33c1913de1be35"  # VNPAY
    MOMO_ID = "6080f319ca33c1913de1be36"  # MOMO
    BANK_CARD_ID = "632aca6e2c2071e01556e978"  # BANK_CARD
    MASTERCARD_VISA_ID = "632acad12c2071e01556e979"  # MASTERCARD_VISA
    ONEPAY_ID = "67c1433d444943956c790309"  # ONEPAY
    MASTERCARD_VISA_ONEPAY_ID = "67d3926bbfaa50609c736fb9"  # MASTERCARD_VISA_ONEPAY
    BANK_CARD_ONEPAY_ID = "67d39243bfaa50609c736fb8"  # BANK_CARD_ONEPAY


E_PAYMENT_IDS = [
    PaymentMethodId.VNPAY_ID.value,
    PaymentMethodId.MOMO_ID.value,
    PaymentMethodId.BANK_CARD_ID.value,
    PaymentMethodId.MASTERCARD_VISA_ID.value,
    PaymentMethodId.ONEPAY_ID.value,
    PaymentMethodId.MASTERCARD_VISA_ONEPAY_ID.value,
    PaymentMethodId.BANK_CARD_ONEPAY_ID.value,
]


# Shipping status
class ShippingStatus(Enum):
    PENDING = "pending"
    WAIT_TO_PICK = "wait_to_pick"
    SHIPPING = "shipping"
    SHIPPED = "shipped"
    CANCELING = "canceling"
    CANCELED = "canceled"
    RETURN = "return"
    RETURNING = "returning"


# Payment status
class PaymentStatus(Enum):
    PAID = "paid"
    PENDING = "pending"


def get_payment_method_name(payment_method_id: str) -> str:
    if payment_method_id == PaymentMethodId.CASH_ID.value:
        return "cash"
    if payment_method_id in E_PAYMENT_IDS:
        return "epay"
    return unknown