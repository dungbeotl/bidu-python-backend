from bson import ObjectId
from typing import Any
import json
from datetime import datetime
from beanie import Document


def serialize_object_id(obj: Any) -> Any:
    """
    Chuyển đổi ObjectId thành string và xử lý các cấu trúc lồng nhau.
    Hỗ trợ cả Beanie Document và cấu trúc dữ liệu thông thường.
    """
    if obj is None:
        return None

    # Xử lý Document của Beanie
    if isinstance(obj, Document):
        # Sử dụng dict() của Beanie để chuyển đổi
        return serialize_object_id(obj.dict())

    if isinstance(obj, ObjectId):
        return str(obj)

    if isinstance(obj, list) or isinstance(obj, tuple):
        return [serialize_object_id(item) for item in obj]

    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}

    if isinstance(obj, datetime):
        return obj.isoformat()

    # Các kiểu dữ liệu khác (int, bool, string,...) trả về nguyên bản
    return obj


class MongoJSONEncoder(json.JSONEncoder):
    """
    JSON Encoder xử lý các kiểu dữ liệu MongoDB và Beanie.
    """

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Document):
            return serialize_object_id(obj.dict())
        return super().default(obj)


def convert_mongo_document(data: Any) -> Any:
    """
    Chuyển đổi dữ liệu từ MongoDB/Beanie để sử dụng trong response API.

    Hỗ trợ:
    - Document của Beanie
    - Dictionary thông thường
    - List các document/dict
    - ObjectId

    Args:
        data: Dữ liệu cần chuyển đổi (Document, dict, list, etc.)

    Returns:
        Dữ liệu đã được chuyển đổi
    """
    if data is None:
        return None

    return serialize_object_id(data)
