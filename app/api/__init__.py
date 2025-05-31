"""
Module API chứa tất cả các routes và dependencies liên quan đến API.
"""

# Export dependencies
from .dependencies import (
    get_current_user,
    get_current_superuser,
    get_current_active_user,
)

# Export routes
from .routes import auth, export, users, recommendation
