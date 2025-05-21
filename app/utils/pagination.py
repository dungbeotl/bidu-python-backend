from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorCollection

async def aggregate_paginate(
    collection: AsyncIOMotorCollection, 
    pipeline: List[Dict[str, Any]], 
    page: int = 1, 
    limit: int = 1
) -> Dict[str, Any]:
    """
    Thực hiện phân trang kết quả từ MongoDB aggregation pipeline.
    
    Args:
        collection: MongoDB collection.
        pipeline: Aggregation pipeline.
        page: Số trang hiện tại (bắt đầu từ 1).
        limit: Số lượng document trên mỗi trang.
        
    Returns:
        Dictionary chứa kết quả đã phân trang và metadata.
    """
    # Đảm bảo page luôn >= 1
    if page < 1:
        page = 1
        
    # Đảm bảo limit luôn > 0
    if limit < 1:
        limit = 1
        
    # Tính skip dựa trên page và limit
    skip = (page - 1) * limit
    
    # Clone pipeline
    data_pipeline = pipeline + [
        {"$skip": skip},
        {"$limit": limit}
    ]
    
    # Pipeline để đếm tổng số document
    count_pipeline = pipeline + [
        {"$count": "total"}
    ]
    
    # Thực hiện queries
    data_cursor = collection.aggregate(data_pipeline)
    count_cursor = collection.aggregate(count_pipeline)
    
    # Lấy kết quả
    data = await data_cursor.to_list(length=limit)
    count_result = await count_cursor.to_list(length=1)
    
    # Tính tổng số document
    total = count_result[0]["total"] if count_result else 0
    
    # Tính tổng số trang (làm tròn lên)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Trả về kết quả định dạng chuẩn
    return {
        "docs": data,
        "total_docs": total,
        "limit": limit,
        "page": page,
        "total_pages": total_pages,
        "has_next_page": (page * limit) < total,
        "has_prev_page": page > 1,
        "next_page": page + 1 if (page * limit) < total else None,
        "prev_page": page - 1 if page > 1 else None,
        "paging_counter": skip + 1,  # Số thứ tự của document đầu tiên
    }