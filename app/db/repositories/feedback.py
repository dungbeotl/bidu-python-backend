from app.db.repositories import BaseRepository
from app.models import Feedback
from app.utils import convert_mongo_document
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from beanie.odm.fields import PydanticObjectId
from datetime import datetime


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository cho collection feedbacks sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Feedback Repository."""
        super().__init__(Feedback)

    async def get_all_feedback(self, target_type: str):
        """Lấy tất cả các feedback."""

        pipline = [
            {"$match": {"target_type": target_type}},
            {
                "$project": {
                    "_id": 1,
                    "content": 1,
                    "vote_star": 1,
                    "target_id": 1,
                    "shop_id": 1,
                    "user_id": 1,
                    "created_at": 1,
                }
            },
        ]
        feedbacks_raw = await self.model.aggregate(
            pipline,
            allowDiskUse=True,
        ).to_list()

        return convert_mongo_document(feedbacks_raw)
