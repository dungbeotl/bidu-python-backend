"""
Module database chứa tất cả các thành phần liên quan đến DB.
"""

# Export các kết nối DB
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.redis_db import redis  # Export redis client thay vì get_redis

# Export các repositories
from app.db.repositories import UserRepository, ProductRepository, AddressRepository
