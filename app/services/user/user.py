from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from fastapi.responses import StreamingResponse
from app.core.exceptions import (
    BadRequestException,
    DatabaseException,
)
from app.db.repositories import UserRepository
from app.services import BaseService, AddressService
from app.utils import ExportUtil, to_hashmap, to_lower_strip
from app.constants import unknown

logger = logging.getLogger(__name__)


class UserService(BaseService[UserRepository]):
    """Service for user operations."""

    def __init__(self):
        """Khởi tạo UserService."""
        # Gọi constructor của base class
        super().__init__(repository=UserRepository(), es_index="users")

    # Phương thức lấy danh sách tất cả người dùng
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Lấy danh sách tất cả người dùng với phân trang.

        Args:
            skip: Số lượng bản ghi bỏ qua.
            limit: Số lượng bản ghi tối đa trả về.

        Returns:
            Danh sách các dictionary chứa dữ liệu người dùng.

        Raises:
            DatabaseException: Nếu có lỗi khi truy vấn cơ sở dữ liệu.
        """
        try:
            # Lấy tất cả người dùng từ database
            users = await self.repository.get_all_with_pagination(
                limit=limit, skip=skip
            )
            # Sử dụng _prepare_data thừa kế từ BaseService để xử lý serialization
            return await self.prepare_list_data(users)
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise DatabaseException(
                detail=f"Lỗi khi lấy danh sách người dùng: {str(e)}"
            )

    # ************* FUNCTION for AWS personalize ************* #

    async def _export_to_format(self, data: List[Dict[str, Any]], format: str) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Helper method để export dữ liệu theo format, tránh dư thừa code.
        
        Args:
            data: Dữ liệu đã được xử lý
            format: Định dạng xuất (json, csv)
            
        Returns:
            StreamingResponse hoặc dict thông tin
        """
        # Kiểm tra nếu không có dữ liệu
        if not data:
            return {"success": False, "message": "Không có dữ liệu người dùng"}

        # Sử dụng _prepare_data để đảm bảo tất cả ObjectId đã được xử lý
        processed_data = self._prepare_data(data)

        # Xử lý xuất theo định dạng
        if format.lower() == "json":
            return await ExportUtil()._export_dataset_to_json(processed_data)
        elif format.lower() == "csv":
            return await ExportUtil()._export_dataset_to_csv(processed_data)
        else:
            raise BadRequestException(
                detail=f"Định dạng {format} không được hỗ trợ"
            )

    async def export_users_for_personalize(
        self,
        format: str = "json",
        limit: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        personalize_format: str = "custom",
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Xuất dữ liệu người dùng cho AWS Personalize.

        Args:
            format: Định dạng xuất (json, csv).
            limit: Số lượng người dùng tối đa (None = tất cả).
            filter_dict: Bộ lọc bổ sung.
            personalize_format: Loại format (custom, ecommerce).

        Returns:
            StreamingResponse với dữ liệu định dạng hoặc dict thông tin.
        """
        try:
            # Lấy dữ liệu dựa trên personalize_format
            if personalize_format == "ecommerce":
                users_data = await self.get_users_for_personalize_ecommerce(
                    limit=limit, filter_dict=filter_dict
                )
            else:  # default to custom
                users_data = await self.get_users_for_personalize(
                    limit=limit, filter_dict=filter_dict
                )

            return await self._export_to_format(users_data, format)

        except Exception as e:
            logger.error(f"Error exporting users for personalize: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất dữ liệu người dùng: {str(e)}")

    async def get_users_for_personalize(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu người dùng được định dạng cho AWS Personalize.
        """
        try:
            # Lấy dữ liệu từ repository
            users_data = await self.repository.get_users_for_personalize(
                limit=limit, filter_dict=filter_dict
            )
            print("Get users for personalize: ", len(users_data))

            # Lấy tất cả địa chỉ có is_default là True
            address_service = AddressService()
            address_raw = await address_service.get_all_addresses()
            address_hashmap = to_hashmap(data=address_raw, key="accessible_id")

            processed_users = []

            print("Start processing users for personalize...")
            # Xử lý dữ liệu
            now = datetime.utcnow()
            for user in users_data:
                user_id = user["_id"]

                # Xử lý gender
                gender = "unisex"
                if "gender" in user and user["gender"]:
                    gender_map = {1: "male", 2: "female", 3: "unisex"}
                    gender = gender_map.get(user["gender"], None)

                # Xử lý age_group - Sử dụng trường "birthday" thay vì "dateOfBirth"
                age_group = unknown
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
                        age_group = unknown

                # Xử lý membership_duration
                membership_duration = unknown
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
                        membership_duration = unknown

                # Xử lý location từ default_address
                address = address_hashmap.get(user_id)
                location = self._get_address_for_user(address)
                # if address:
                #     try:
                #         # Xử lý location từ state nếu có
                #         if (
                #             "state" in address
                #             and address["state"]
                #             and "name" in address["state"]
                #         ):
                #             location = address["state"]["name"]
                #     except Exception:
                #         location = unknown

                # Xây dựng đối tượng user cho personalize
                personalize_user = {
                    "USER_ID": user_id,
                    "GENDER": gender,
                    "AGE_GROUP": age_group,
                    "MEMBERSHIP_DURATION": membership_duration,
                    "LOCATION": to_lower_strip(location),
                }

                processed_users.append(personalize_user)

            print("Processed users for personalize: ", len(processed_users))

            return processed_users
        except Exception as e:
            logger.error(f"Error getting users for personalize: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi lấy dữ liệu người dùng: {str(e)}")

    def _get_address_for_user(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lấy địa chỉ cho user.
        """
        if (
            address
            and "state" in address
            and address["state"]
            and "name" in address["state"]
        ):
            return address["state"]["name"]
        return unknown

    async def get_users_for_personalize_ecommerce(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu người dùng được định dạng cho AWS Personalize với format ecommerce đơn giản.
        Format ecommerce: USER_ID, GENDER.
        """
        try:
            # Lấy dữ liệu từ repository
            users_data = await self.repository.get_users_for_personalize_ecommerce(
                limit=limit, filter_dict=filter_dict
            )
            print("Get users for personalize ecommerce: ", len(users_data))

            processed_users = []

            print("Start processing users for personalize ecommerce...")
            # Xử lý dữ liệu - lấy USER_ID và GENDER
            for user in users_data:
                user_id = user["_id"]

                # Xử lý gender
                gender = "unisex"
                if "gender" in user and user["gender"]:
                    gender_map = {1: "male", 2: "female", 3: "unisex"}
                    gender = gender_map.get(user["gender"], "unisex")

                # Xây dựng đối tượng user cho personalize với format ecommerce
                personalize_user = {
                    "USER_ID": user_id,
                    "GENDER": gender,
                }

                processed_users.append(personalize_user)

            print("Processed users for personalize ecommerce: ", len(processed_users))

            return processed_users
        except Exception as e:
            logger.error(f"Error getting users for personalize ecommerce: {str(e)}")
            raise DatabaseException(
                detail=f"Lỗi khi lấy dữ liệu người dùng ecommerce: {str(e)}"
            )
