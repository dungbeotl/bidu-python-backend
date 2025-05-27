from app.services import BaseService
from app.db.repositories import AddressRepository
from typing import List, Dict, Any


class AddressService(BaseService[AddressRepository]):
    """Service for address operations."""

    def __init__(self):
        """Khởi tạo ProductService."""
        super().__init__(repository=AddressRepository())

    async def get_all_addresses(self) -> List[Dict[str, Any]]:
        """Lấy tất cả địa chỉ."""
        return await self.repository.get_all_addresses()
