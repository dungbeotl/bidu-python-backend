"""
Module chứa các schema Pydantic cho API.
"""

# Export các schema chính
from app.schemas.user import (
    UserSchema, 
    UserCreateSchema, 
    UserUpdateSchema, 
    UserMinimalSchema
)

from app.schemas.product import (
    ProductSchema, 
    ProductDetailSchema, 
    ProductListSchema
)

from app.schemas.address import (
    AddressCreate,
    AddressUpdate,
    AddressOut
)