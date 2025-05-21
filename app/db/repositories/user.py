from typing import Dict, List, Optional, Any
from bson import ObjectId
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from app.core import get_password_hash, verify_password
from app.db.repositories import BaseRepository
from app.models import User
from app.utils import convert_mongo_document


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
        pipeline.append(
            {
                "$lookup": {
                    "from": "addresses",  # Tên collection
                    "let": {"user_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$accessible_id", "$$user_id"]},
                                        {"$eq": ["$is_default", True]},
                                    ]
                                }
                            }
                        },
                        {"$limit": 1},
                    ],
                    "as": "default_address",
                }
            }
        )

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
        raw_users = await User.aggregate(pipeline).to_list()
        serialized_users = convert_mongo_document(raw_users)
        processed_users = []

        # Xử lý dữ liệu
        now = datetime.utcnow()
        for user in serialized_users:
            user_id = user["_id"]

            # Xử lý gender
            gender = "other"
            if "gender" in user and user["gender"]:
                gender_map = {1: "male", 2: "female", 3: "other"}
                gender = gender_map.get(user["gender"], None)

            # Xử lý age_group - Sử dụng trường "birthday" thay vì "dateOfBirth"
            age_group = "UNKNOWN"
            if "birthday" in user and user["birthday"]:
                try:
                    # Xử lý birthday dạng string "DD/MM/YYYY"
                    if isinstance(user["birthday"], str):
                        # Phân tách ngày, tháng, năm
                        day, month, year = user["birthday"].split("/")
                        # Chuyển đổi thành đối tượng datetime
                        dob = datetime(int(year), int(month), int(day))
                    else:
                        # Trường hợp birthday đã là đối tượng datetime
                        dob = user["birthday"]

                    # Tính tuổi
                    age = relativedelta(now, dob).years

                    if age < 18:
                        age_group = "under_18"
                    elif age <= 24:
                        age_group = "18-24"
                    elif age <= 34:
                        age_group = "25-34"
                    elif age <= 44:
                        age_group = "35-44"
                    else:
                        age_group = "45+"
                except Exception as e:
                    # Log lỗi nếu cần
                    print(f"Error processing birthday: {str(e)}")
                    # Nếu có lỗi khi tính tuổi, sử dụng giá trị mặc định
                    age_group = "UNKNOWN"

            # Xử lý membership_duration
            membership_duration = "UNKNOWN"
            if "createdAt" in user and user["createdAt"]:
                try:
                    created_at = user["createdAt"]
                    months = (now.year - created_at.year) * 12 + (
                        now.month - created_at.month
                    )

                    if months < 6:
                        membership_duration = "0-6_months"
                    elif months < 12:
                        membership_duration = "6-12_months"
                    elif months < 24:
                        membership_duration = "1-2_years"
                    else:
                        membership_duration = "2+_years"
                except Exception:
                    # Nếu có lỗi khi tính thời gian, sử dụng giá trị mặc định
                    membership_duration = "UNKNOWN"

            # Xử lý location từ default_address
            location = "UNKNOWN"
            if (
                "default_address" in user
                and isinstance(user["default_address"], list)
                and len(user["default_address"]) > 0
            ):
                try:
                    # Lấy địa chỉ đầu tiên từ mảng
                    address = user["default_address"][0]

                    # Xử lý location từ state nếu có
                    if (
                        "state" in address
                        and address["state"]
                        and "name" in address["state"]
                    ):
                        location = address["state"]["name"]
                except Exception:
                    # Nếu có lỗi khi xử lý địa chỉ, sử dụng giá trị mặc định
                    location = "UNKNOWN"

            # Xây dựng đối tượng user cho personalize
            personalize_user = {
                "USER_ID": user_id,
                "gender": gender,
                "age_group": age_group,
                "membership_duration": membership_duration,
                "location": location,
            }

            processed_users.append(personalize_user)

        return processed_users
