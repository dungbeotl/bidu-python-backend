from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from bson import ObjectId


class MongoModel(BaseModel):
    """
    Base model cho các model với dữ liệu từ MongoDB.

    Tự động cấu hình để làm việc tốt với các kiểu dữ liệu MongoDB.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    # Hỗ trợ chuyển đổi _id <-> id
    id: Optional[Any] = Field(None, alias="_id")

    def model_dump_mongo(self) -> Dict:
        """
        Dump model thành dict phù hợp với MongoDB.
        Xử lý đặc biệt các trường như id -> _id
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        return data
