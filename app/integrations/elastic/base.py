# app/services/base_elasticsearch.py

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import logging
from datetime import datetime
from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch, NotFoundError

from app.core.exceptions import NotFoundException, DatabaseException
from app.db.elasticsearch_db import es

# Type variable cho Model
M = TypeVar("M", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseElasticsearchService(Generic[M]):
    """Base service cho Elasticsearch."""

    def __init__(self, index_name: str, model_class: Type[M]):
        """
        Khởi tạo Elasticsearch service.

        Args:
            index_name: Tên của index trong Elasticsearch.
            model_class: Pydantic model class đại diện cho document.
        """
        self.index_name = index_name
        self.model_class = model_class
        self.client = es.client

    async def create_index(
        self, settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tạo index trong Elasticsearch.

        Args:
            settings: Cấu hình cho index.

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            # Nếu không có settings cụ thể, sử dụng cấu hình mặc định
            if settings is None:
                # Tự động sinh mappings từ model
                properties = {}
                for field_name, field in self.model_class.__fields__.items():
                    # Xác định kiểu dữ liệu Elasticsearch tương ứng
                    if field.type_ == str:
                        field_type = "text"
                    elif field.type_ == int:
                        field_type = "integer"
                    elif field.type_ == float:
                        field_type = "float"
                    elif field.type_ == bool:
                        field_type = "boolean"
                    elif field.type_ == datetime:
                        field_type = "date"
                    else:
                        field_type = "keyword"

                    # Thêm vào properties
                    properties[field_name] = {"type": field_type}

                # Tạo settings
                settings = {
                    "mappings": {"properties": properties},
                    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                }

            # Tạo index
            response = await self.client.indices.create(
                index=self.index_name,
                body=settings,
                ignore=400,  # Bỏ qua lỗi nếu index đã tồn tại
            )

            return response
        except Exception as e:
            logger.error(f"Error creating index {self.index_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi tạo index: {str(e)}")

    async def delete_index(self) -> Dict[str, Any]:
        """
        Xóa index trong Elasticsearch.

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            response = await self.client.indices.delete(
                index=self.index_name,
                ignore=[404],  # Bỏ qua lỗi nếu index không tồn tại
            )

            return response
        except Exception as e:
            logger.error(f"Error deleting index {self.index_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi xóa index: {str(e)}")

    async def index_document(
        self, doc_id: str, document: Union[Dict[str, Any], M]
    ) -> Dict[str, Any]:
        """
        Lưu document vào Elasticsearch.

        Args:
            doc_id: ID của document.
            document: Dictionary hoặc Model chứa dữ liệu.

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            # Chuyển Model thành dict nếu cần
            if isinstance(document, BaseModel):
                document = document.dict()

            # Index document
            response = await self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document,
                refresh="wait_for",  # Đảm bảo document có thể tìm kiếm ngay lập tức
            )

            return response
        except Exception as e:
            logger.error(
                f"Error indexing document {doc_id} to {self.index_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi lưu document: {str(e)}")

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy document từ Elasticsearch theo ID.

        Args:
            doc_id: ID của document.

        Returns:
            Document nếu tìm thấy, None nếu không tìm thấy.
        """
        try:
            response = await self.client.get(index=self.index_name, id=doc_id)

            return response["_source"]
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(
                f"Error getting document {doc_id} from {self.index_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi lấy document: {str(e)}")

    async def update_document(
        self, doc_id: str, document: Union[Dict[str, Any], M]
    ) -> Dict[str, Any]:
        """
        Cập nhật document trong Elasticsearch.

        Args:
            doc_id: ID của document.
            document: Dictionary hoặc Model chứa dữ liệu cập nhật.

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            # Chuyển Model thành dict nếu cần
            if isinstance(document, BaseModel):
                document = document.dict(exclude_unset=True)

            # Update document
            response = await self.client.update(
                index=self.index_name,
                id=doc_id,
                body={"doc": document},
                refresh="wait_for",  # Đảm bảo document có thể tìm kiếm ngay lập tức
            )

            return response
        except NotFoundError:
            raise NotFoundException(detail=f"Document không tồn tại: {doc_id}")
        except Exception as e:
            logger.error(
                f"Error updating document {doc_id} in {self.index_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi cập nhật document: {str(e)}")

    async def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Xóa document từ Elasticsearch.

        Args:
            doc_id: ID của document.

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            response = await self.client.delete(
                index=self.index_name,
                id=doc_id,
                refresh="wait_for",  # Đảm bảo document được xóa ngay lập tức
            )

            return response
        except NotFoundError:
            raise NotFoundException(detail=f"Document không tồn tại: {doc_id}")
        except Exception as e:
            logger.error(
                f"Error deleting document {doc_id} from {self.index_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi xóa document: {str(e)}")

    async def search_documents(
        self,
        query: Dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Tìm kiếm documents trong Elasticsearch.

        Args:
            query: Dictionary chứa query Elasticsearch.
            from_: Vị trí bắt đầu.
            size: Số lượng kết quả tối đa trả về.
            sort: Danh sách các trường và hướng sắp xếp.

        Returns:
            Kết quả tìm kiếm từ Elasticsearch.
        """
        try:
            body = {"query": query}

            if sort:
                body["sort"] = sort

            response = await self.client.search(
                index=self.index_name, body=body, from_=from_, size=size
            )

            return response
        except Exception as e:
            logger.error(f"Error searching documents in {self.index_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi tìm kiếm documents: {str(e)}")

    async def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Đếm số lượng documents trong Elasticsearch.

        Args:
            query: Dictionary chứa query Elasticsearch.

        Returns:
            Số lượng documents.
        """
        try:
            body = {}
            if query:
                body["query"] = query

            response = await self.client.count(index=self.index_name, body=body)

            return response["count"]
        except Exception as e:
            logger.error(f"Error counting documents in {self.index_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi đếm documents: {str(e)}")

    async def bulk_index(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Lưu nhiều documents vào Elasticsearch cùng lúc.

        Args:
            actions: Danh sách các actions cần thực hiện.
                Mỗi action có format {"id": "...", "document": {...}}

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            if not actions:
                return {"errors": False, "items": []}

            body = []
            for action in actions:
                doc_id = action.get("id")
                document = action.get("document", {})

                # Chuyển Model thành dict nếu cần
                if isinstance(document, BaseModel):
                    document = document.dict()

                # Thêm action vào body
                body.append({"index": {"_index": self.index_name, "_id": doc_id}})
                body.append(document)

            response = await self.client.bulk(
                body=body,
                refresh="wait_for",  # Đảm bảo documents có thể tìm kiếm ngay lập tức
            )

            return response
        except Exception as e:
            logger.error(
                f"Error bulk indexing documents to {self.index_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi lưu hàng loạt documents: {str(e)}")

    async def bulk_update(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cập nhật nhiều documents trong Elasticsearch cùng lúc.

        Args:
            actions: Danh sách các actions cần thực hiện.
                Mỗi action có format {"id": "...", "document": {...}}

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            if not actions:
                return {"errors": False, "items": []}

            body = []
            for action in actions:
                doc_id = action.get("id")
                document = action.get("document", {})

                # Chuyển Model thành dict nếu cần
                if isinstance(document, BaseModel):
                    document = document.dict(exclude_unset=True)

                # Thêm action vào body
                body.append({"update": {"_index": self.index_name, "_id": doc_id}})
                body.append({"doc": document})

            response = await self.client.bulk(
                body=body,
                refresh="wait_for",  # Đảm bảo documents được cập nhật ngay lập tức
            )

            return response
        except Exception as e:
            logger.error(
                f"Error bulk updating documents in {self.index_name}: {str(e)}"
            )
            raise DatabaseException(
                detail=f"Lỗi khi cập nhật hàng loạt documents: {str(e)}"
            )

    async def sync_from_database(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Đồng bộ dữ liệu từ database sang Elasticsearch.

        Args:
            documents: Danh sách các documents cần đồng bộ.
                Mỗi document phải có trường "_id".

        Returns:
            Kết quả từ Elasticsearch.
        """
        try:
            # Tạo danh sách actions
            actions = []
            for document in documents:
                doc_id = str(document.pop("_id", None))
                if not doc_id:
                    continue

                actions.append({"id": doc_id, "document": document})

            # Bulk index
            return await self.bulk_index(actions)
        except Exception as e:
            logger.error(f"Error syncing documents to {self.index_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi đồng bộ dữ liệu: {str(e)}")
