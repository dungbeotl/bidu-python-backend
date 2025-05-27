from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel

from beanie import Document
from beanie.operators import In

from app.utils import aggregate_paginate

# Type variable cho Model
T = TypeVar("T", bound=Document)


class BaseRepository(Generic[T]):
    """Base repository sử dụng Beanie ODM."""

    def __init__(self, model: Type[T]):
        """
        Khởi tạo repository với Beanie Document class.

        Args:
            model: Beanie Document class.
        """
        self.model = model

    async def get(self, id: str) -> Optional[T]:
        """
        Lấy document theo ID.

        Args:
            id: ID của document (string).

        Returns:
            Document nếu tìm thấy, None nếu không tìm thấy.
        """
        try:
            # Chuyển đổi string ID thành ObjectId
            object_id = ObjectId(id) if isinstance(id, str) else id
            return await self.model.get(object_id)
        except:
            return None

    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """
        Lấy document theo một trường cụ thể.

        Args:
            field: Tên trường.
            value: Giá trị của trường.

        Returns:
            Document nếu tìm thấy, None nếu không tìm thấy.
        """
        return await self.model.find_one({field: value})

    async def get_all_with_pagination(self, limit: int = 100, skip: int = 0) -> List[T]:
        """
        Lấy tất cả documents với phân trang.

        Args:
            limit: Số document tối đa trả về.
            skip: Số document bỏ qua.

        Returns:
            Danh sách các documents.
        """
        return await self.model.find_all().skip(skip).limit(limit).to_list()

    async def get_all(self) -> List[T]:
        """
        Lấy tất cả documents.

        Returns:
            Danh sách các documents.
        """
        return await self.model.find_all().to_list()

    async def get_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_dict: Dict[str, Any] = None,
        sort_by: Optional[str] = None,
        sort_order: int = 1,
    ) -> List[T]:
        """
        Lấy documents với filter và sorting.

        Args:
            skip: Số document bỏ qua.
            limit: Số document tối đa trả về.
            filter_dict: Dictionary chứa các điều kiện lọc.
            sort_by: Trường để sắp xếp.
            sort_order: Thứ tự sắp xếp (1: tăng dần, -1: giảm dần).

        Returns:
            Danh sách các documents thỏa mãn điều kiện.
        """
        if filter_dict is None:
            filter_dict = {}

        # Tạo sort dict
        sort_dict = {}
        if sort_by:
            sort_dict[sort_by] = sort_order
        else:
            sort_dict["createdAt"] = -1  # Mặc định sắp xếp theo createdAt giảm dần

        # Query với filter và sorting
        query = self.model.find(filter_dict)

        # Áp dụng sort
        for field, order in sort_dict.items():
            if order == 1:
                query = query.sort(f"+{field}")
            else:
                query = query.sort(f"-{field}")

        # Áp dụng skip và limit
        results = await query.skip(skip).limit(limit).to_list()
        return results

    async def create(self, data: Union[Dict[str, Any], T, BaseModel]) -> T:
        """
        Tạo document mới.

        Args:
            data: Dictionary, Beanie Document hoặc Pydantic Model chứa dữ liệu.

        Returns:
            Document đã tạo với ID.
        """
        # Nếu là dict, tạo đối tượng document từ dict
        if isinstance(data, dict):
            document = self.model(**data)

        # Nếu là pydantic model (nhưng không phải Document)
        elif isinstance(data, BaseModel) and not isinstance(data, Document):
            document = self.model(**data.model_dump())

        # Nếu đã là Document
        else:
            document = data

        # Tự động set timestamp
        if hasattr(document, "createdAt") and document.createdAt is None:
            document.createdAt = datetime.now(timezone.utc)
        if hasattr(document, "updatedAt"):
            document.updatedAt = datetime.now(timezone.utc)

        # Lưu vào database
        await document.insert()
        return document

    async def update(self, id: str, data: Union[Dict[str, Any], BaseModel]) -> bool:
        """
        Cập nhật document.

        Args:
            id: ID của document cần cập nhật.
            data: Dictionary hoặc Model chứa dữ liệu cập nhật.

        Returns:
            True nếu cập nhật thành công, False nếu thất bại.
        """
        # Lấy document hiện tại
        document = await self.get(id)
        if not document:
            return False

        # Chuyển data thành dict nếu cần
        if isinstance(data, BaseModel):
            update_data = data.model_dump(exclude_unset=True)
        else:
            update_data = data

        # Cập nhật timestamp
        if hasattr(document, "updatedAt"):
            update_data["updatedAt"] = datetime.now(timezone.utc)

        # Cập nhật document
        result = await document.update({"$set": update_data})
        return result is not None

    async def delete(self, id: str) -> bool:
        """
        Xóa document.

        Args:
            id: ID của document cần xóa.

        Returns:
            True nếu xóa thành công, False nếu thất bại.
        """
        document = await self.get(id)
        if not document:
            return False

        await document.delete()
        return True

    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """
        Đếm số lượng documents thỏa mãn điều kiện.

        Args:
            filter_dict: Dictionary chứa các điều kiện lọc.

        Returns:
            Số lượng documents thỏa mãn điều kiện.
        """
        if filter_dict is None:
            filter_dict = {}

        return await self.model.find(filter_dict).count()

    async def bulk_create(
        self, data_list: List[Union[Dict[str, Any], BaseModel]]
    ) -> List[T]:
        """
        Tạo nhiều documents cùng lúc.

        Args:
            data_list: Danh sách các Dictionary hoặc Model chứa dữ liệu.

        Returns:
            Danh sách documents đã tạo.
        """
        documents = []
        now = datetime.now(timezone.utc)

        for data in data_list:
            # Chuyển đổi data thành dict nếu cần
            if isinstance(data, BaseModel):
                item_data = data.model_dump(exclude_unset=True)
            else:
                item_data = data.copy()

            # Thêm timestamps nếu model có các trường đó
            if hasattr(self.model, "createdAt"):
                item_data["createdAt"] = now
            if hasattr(self.model, "updatedAt"):
                item_data["updatedAt"] = now

            # Tạo document
            document = self.model(**item_data)
            documents.append(document)

        # Lưu tất cả vào database
        return await self.model.insert_many(documents)

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Cập nhật nhiều documents cùng lúc.

        Args:
            updates: Danh sách các dictionary, mỗi dictionary chứa "id" và "data" để cập nhật.

        Returns:
            Số lượng documents đã cập nhật.
        """
        success_count = 0
        for update in updates:
            id_str = update.get("id")
            data = update.get("data", {})

            if id_str and data:
                success = await self.update(id_str, data)
                if success:
                    success_count += 1

        return success_count

    async def find_by_ids(self, ids: List[str]) -> List[T]:
        """
        Tìm các documents theo danh sách ID.

        Args:
            ids: Danh sách các ID.

        Returns:
            Danh sách các documents thỏa mãn.
        """
        # Chuyển đổi string IDs thành ObjectIds
        object_ids = [ObjectId(id_str) for id_str in ids if ObjectId.is_valid(id_str)]
        if not object_ids:
            return []

        # Sử dụng In operator với trường _id thay vì id
        documents = await self.model.find(
            {"_id": {"$in": object_ids}}
        ).to_list()
        return documents

    async def aggregate_paginate(
        self, pipeline: List[Dict[str, Any]], page: int = 1, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Thực hiện aggregation với phân trang.

        Args:
            pipeline: MongoDB aggregation pipeline.
            page: Số trang.
            limit: Số document mỗi trang.

        Returns:
            Dictionary chứa kết quả và metadata phân trang.
        """
        # Beanie hỗ trợ aggregation qua motor
        collection = self.model.get_motor_collection()
        result = await aggregate_paginate(collection, pipeline, page, limit)
        return result
