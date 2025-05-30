"""
Module services chứa logic nghiệp vụ của ứng dụng.
"""

from typing import TYPE_CHECKING

# Import BaseService trước vì nó là dependency cơ bản
from .base import BaseService

# Import các service theo thứ tự dependency
# AddressService không phụ thuộc vào service nào khác (ngoài BaseService)
from .address import AddressService

# ProductService và InteractionService
from .product import ProductService
from .interaction import InteractionService

# UserService import cuối cùng vì nó phụ thuộc vào AddressService
from .user import UserService

# OrderService
from .order import OrderService

# ShopService
from .shop import ShopService

# Export tất cả
__all__ = [
    'BaseService',
    'AddressService',
    'ProductService', 
    'InteractionService',
    'UserService',
    'OrderService',
    'ShopService',
]
