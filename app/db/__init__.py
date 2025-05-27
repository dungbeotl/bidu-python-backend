"""
Module database chứa tất cả các thành phần liên quan đến DB.
"""

# Export các kết nối DB
from .mongodb import connect_to_mongo, close_mongo_connection
from .redis_db import redis  # Export redis client thay vì get_redis
from .firebase import FirebaseDB, firebase_db

# Export các repositories
from .repositories import (
    UserRepository,
    ProductRepository,
    AddressRepository,
    # OrderItemRepository,
)
