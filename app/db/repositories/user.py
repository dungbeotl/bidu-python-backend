from typing import Dict, List, Optional, Any
from bson import ObjectId
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from app.core import get_password_hash, verify_password
from app.db.repositories.base import BaseRepository
from app.models import User
from app.utils import convert_mongo_document
from app.constants import unknown


class UserRepository(BaseRepository[User]):
    """Repository cho collection users sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo User Repository."""
        super().__init__(User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Lấy user theo email.

        Args:
            email: Email của user.

        Returns:
            User nếu tìm thấy, None nếu không tìm thấy.
        """
        return await User.find_one({"email": email})

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Xác thực user bằng email và password.

        Args:
            email: Email của user.
            password: Password chưa hash.

        Returns:
            User nếu xác thực thành công, None nếu thất bại.
        """
        user = await self.get_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    # FUNCTION for AWS personalize

    async def get_users_for_personalize(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu người dùng được định dạng cho AWS Personalize.

        Args:
            limit: Số lượng người dùng tối đa (None = tất cả).
            skip: Số người dùng bỏ qua.
            filter_dict: Bộ lọc bổ sung.

        Returns:
            Danh sách người dùng đã được xử lý.
        """
        # Xác định pipeline
        pipeline = []

        # Thêm bộ lọc nếu có
        if filter_dict:
            pipeline.append({"$match": filter_dict})

        # Thêm stage để lookup address
        # pipeline.append(
        #     {
        #         "$lookup": {
        #             "from": "addresses",
        #             "let": {"user_id": {"$toString": "$_id"}},
        #             "pipeline": [
        #                 {
        #                     "$match": {
        #                         "$expr": {
        #                             "$and": [
        #                                 {"$eq": ["$accessible_id", "$$user_id"]},
        #                                 {"$eq": ["$is_default", True]},
        #                             ]
        #                         }
        #                     }
        #                 },
        #                 {"$limit": 1},
        #             ],
        #             "as": "default_address",
        #         }
        #     }
        # )

        # Project để chỉ lấy các fields cần thiết
        pipeline.append(
            {
                "$project": {
                    "_id": 1,
                    "gender": 1,
                    "birthday": 1,
                    "createdAt": 1,
                    "default_address": 1,
                }
            }
        )

        # Thêm pagination
        if skip > 0:
            pipeline.append({"$skip": skip})

        if limit is not None:
            pipeline.append({"$limit": limit})

        # Thực hiện aggregation với Beanie
        raw_users = await User.aggregate(pipeline, allowDiskUse=True).to_list()
        return convert_mongo_document(raw_users)
