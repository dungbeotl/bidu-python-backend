from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

from app.db.repositories import BaseRepository
from app.models import Address


class AddressRepository(BaseRepository[Address]):
    """Repository cho collection addresses sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Address Repository."""
        super().__init__(Address)

    async def get_by_user_id(self, user_id: str) -> List[Address]:
        """
        Lấy tất cả địa chỉ của một user.

        Args:
            user_id: ID của user.

        Returns:
            Danh sách các địa chỉ.
        """
        return await Address.find(
            {"accessible_id": user_id, "accessible_type": "User"}
        ).to_list()

    async def get_default_address(self, user_id: str) -> Optional[Address]:
        """
        Lấy địa chỉ mặc định của user.

        Args:
            user_id: ID của user.

        Returns:
            Địa chỉ mặc định nếu có, None nếu không.
        """
        return await Address.find_one(
            {"accessible_id": user_id, "accessible_type": "User", "is_default": True}
        )

    async def get_delivery_default_address(self, user_id: str) -> Optional[Address]:
        """
        Lấy địa chỉ giao hàng mặc định.

        Args:
            user_id: ID của user.

        Returns:
            Địa chỉ giao hàng mặc định nếu có, None nếu không.
        """
        return await Address.find_one(
            {
                "accessible_id": user_id,
                "accessible_type": "User",
                "is_delivery_default": True,
            }
        )

    async def create_address(self, address_data: Dict) -> Address:
        """
        Tạo địa chỉ mới.

        Args:
            address_data: Dictionary chứa dữ liệu địa chỉ.

        Returns:
            Address đã tạo.
        """
        # Thiết lập thời gian
        now = datetime.now()
        address_data["created_at"] = now
        address_data["updated_at"] = now

        # Kiểm tra xem có cần set địa chỉ này làm mặc định không
        is_first_address = (
            len(await self.get_by_user_id(address_data.get("accessible_id", ""))) == 0
        )

        if is_first_address:
            address_data["is_default"] = True
            address_data["is_delivery_default"] = True

        # Tạo và lưu địa chỉ
        address = Address(**address_data)
        await address.insert()

        # Nếu địa chỉ này được đánh dấu là mặc định, cập nhật các địa chỉ khác
        if address.is_default:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_default"
            )

        if address.is_delivery_default:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_delivery_default"
            )

        if address.is_pick_address_default:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_pick_address_default"
            )

        if address.is_return_address_default:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_return_address_default"
            )

        return address

    async def update_address(
        self, address_id: str, update_data: Dict
    ) -> Optional[Address]:
        """
        Cập nhật địa chỉ.

        Args:
            address_id: ID của địa chỉ.
            update_data: Dictionary chứa dữ liệu cập nhật.

        Returns:
            Address đã cập nhật nếu thành công, None nếu không.
        """
        # Lấy địa chỉ hiện tại
        address = await self.get(address_id)
        if not address:
            return None

        # Cập nhật thời gian
        update_data["updated_at"] = datetime.now()

        # Cập nhật địa chỉ
        await address.update({"$set": update_data})

        # Nếu địa chỉ này được đánh dấu là mặc định, cập nhật các địa chỉ khác
        need_reload = False

        if "is_default" in update_data and update_data["is_default"]:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_default"
            )
            need_reload = True

        if "is_delivery_default" in update_data and update_data["is_delivery_default"]:
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_delivery_default"
            )
            need_reload = True

        if (
            "is_pick_address_default" in update_data
            and update_data["is_pick_address_default"]
        ):
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_pick_address_default"
            )
            need_reload = True

        if (
            "is_return_address_default" in update_data
            and update_data["is_return_address_default"]
        ):
            await self.update_other_default_addresses(
                address.id, address.accessible_id, "is_return_address_default"
            )
            need_reload = True

        # Reload địa chỉ nếu cần
        if need_reload:
            return await self.get(address_id)

        return address

    async def update_other_default_addresses(
        self, current_id: Any, user_id: str, default_field: str
    ) -> None:
        """
        Cập nhật các địa chỉ khác để đảm bảo chỉ có một địa chỉ mặc định.

        Args:
            current_id: ID của địa chỉ hiện tại (sẽ được giữ lại giá trị mặc định).
            user_id: ID của user.
            default_field: Tên trường mặc định cần cập nhật.
        """
        # Chuyển current_id thành ObjectId nếu là string
        object_id = current_id
        if isinstance(current_id, str) and ObjectId.is_valid(current_id):
            object_id = ObjectId(current_id)

        # Tìm tất cả địa chỉ khác của user mà đang được đánh dấu là mặc định
        filter_query = {
            "accessible_id": user_id,
            "accessible_type": "User",
            "_id": {"$ne": object_id},
            default_field: True,
        }

        # Sử dụng update_many để cập nhật tất cả các địa chỉ khác
        collection = Address.get_motor_collection()
        await collection.update_many(filter_query, {"$set": {default_field: False}})

    async def soft_delete(self, address_id: str) -> bool:
        """
        Xóa mềm địa chỉ bằng cách cập nhật trường deleted_at.

        Args:
            address_id: ID của địa chỉ.

        Returns:
            True nếu xóa thành công, False nếu không.
        """
        address = await self.get(address_id)
        if not address:
            return False

        now = datetime.now()
        await address.update({"$set": {"deleted_at": now, "updated_at": now}})
        return True
