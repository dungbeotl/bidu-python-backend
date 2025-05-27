from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

from app.models import (
    User,
    Product,
    Address,
    ECategory,
    OrderItem,
    Feedback,
    Shop,
    Order,
)


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None


db = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB và khởi tạo Beanie."""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]

    # Khởi tạo Beanie với tất cả Document models
    await init_beanie(
        database=db.db,
        document_models=[
            User,
            Product,
            Address,
            ECategory,
            OrderItem,
            Feedback,
            Shop,
            Order,
            # Thêm các Document models khác ở đây nếu cần
        ],
    )

    print("Connected to MongoDB with Beanie ODM!")


async def close_mongo_connection():
    """Close MongoDB connection."""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection!")
