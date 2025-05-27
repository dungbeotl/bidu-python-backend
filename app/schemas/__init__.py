"""
Module chứa các schema Pydantic cho API.
"""

# Export các schema chính
from .user import UserSchema, UserCreateSchema, UserUpdateSchema, UserMinimalSchema

from .product import ProductSchema, ProductDetailSchema, ProductListSchema

from .address import AddressCreate, AddressUpdate, AddressOut

from .order_item import OrderItemSchema
