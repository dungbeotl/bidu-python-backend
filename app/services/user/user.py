from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging
from fastapi.responses import StreamingResponse
import io
import csv
import json
from app.core.exceptions import (
    BadRequestException,
    DatabaseException,
)
from app.db.repositories import UserRepository
from app.services import BaseService

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

    async def export_users_for_personalize(
        self,
        format: str = "json",
        limit: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Xuất dữ liệu người dùng cho AWS Personalize.

        Args:
            format: Định dạng xuất (json, csv).
            limit: Số lượng người dùng tối đa (None = tất cả).
            filter_dict: Bộ lọc bổ sung.

        Returns:
            StreamingResponse với dữ liệu định dạng hoặc dict thông tin.
        """
        try:
            # Lấy dữ liệu từ repository
            users_data = await self.repository.get_users_for_personalize(
                limit=limit, filter_dict=filter_dict
            )

            # Kiểm tra nếu không có dữ liệu
            if not users_data:
                return {"success": False, "message": "Không có dữ liệu người dùng"}

            # Sử dụng _prepare_data để đảm bảo tất cả ObjectId đã được xử lý
            processed_data = self._prepare_data(users_data)

            # Xử lý xuất theo định dạng
            if format.lower() == "json":
                return await self._export_personalize_to_json(processed_data)
            elif format.lower() == "csv":
                return await self._export_personalize_to_csv(processed_data)
            else:
                raise BadRequestException(
                    detail=f"Định dạng {format} không được hỗ trợ"
                )

        except Exception as e:
            logger.error(f"Error exporting users for personalize: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xuất dữ liệu người dùng: {str(e)}")

    async def _export_personalize_to_json(
        self, users_data: List[Dict[str, Any]]
    ) -> StreamingResponse:
        """
        Xuất dữ liệu người dùng cho AWS Personalize dưới dạng JSON.

        Args:
            users_data: Danh sách người dùng đã xử lý.

        Returns:
            StreamingResponse với dữ liệu JSON.
        """
        # AWS Personalize yêu cầu mỗi record trên một dòng không có dấu phẩy ở cuối
        jsonl_output = ""
        for user in users_data:
            jsonl_output += json.dumps(user) + "\n"

        # Trả về response
        return StreamingResponse(
            iter([jsonl_output]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=users_personalize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            },
        )

    async def _export_personalize_to_csv(
        self, users_data: List[Dict[str, Any]]
    ) -> StreamingResponse:
        """
        Xuất dữ liệu người dùng cho AWS Personalize dưới dạng CSV.

        Args:
            users_data: Danh sách người dùng đã xử lý.

        Returns:
            StreamingResponse với dữ liệu CSV.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Viết header
        if users_data:
            writer.writerow(users_data[0].keys())

        # Viết dữ liệu
        for user in users_data:
            writer.writerow(user.values())

        # Reset về đầu file
        output.seek(0)

        # Trả về response
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=users_personalize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
