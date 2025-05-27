from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import logging
from datetime import datetime
from pydantic import BaseModel
from google.cloud.firestore import Client, DocumentReference, CollectionReference, Query
from google.cloud.firestore import SERVER_TIMESTAMP
from firebase_admin import db

from app.core.exceptions import NotFoundException, DatabaseException
from app.db.firebase_db import firebase_db

# Type variable cho Model
M = TypeVar("M", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseFirestoreService(Generic[M]):
    """Base service cho Firestore."""

    def __init__(self, collection_name: str, model: Type[M]):
        """
        Khởi tạo Firestore service.

        Args:
            collection_name: Tên collection trong Firestore.
            model: Pydantic model class đại diện cho document.
        """
        self.collection_name = collection_name
        self.model = model

    @property
    def client(self) -> Client:
        """Lấy Firestore client."""
        return firebase_db.firestore

    @property
    def collection(self) -> CollectionReference:
        """Lấy collection reference."""
        return self.client.collection(self.collection_name)

    def _model_to_dict(self, model: M) -> Dict[str, Any]:
        """
        Chuyển Model thành dict để lưu vào Firestore.

        Args:
            model: Pydantic model instance.

        Returns:
            Dictionary representation của model.
        """
        data = model.model_dump(exclude_none=True)

        # Thêm timestamp nếu cần
        if hasattr(model, "created_at") and not data.get("created_at"):
            data["created_at"] = SERVER_TIMESTAMP
        if hasattr(model, "updated_at"):
            data["updated_at"] = SERVER_TIMESTAMP

        return data

    def _dict_to_model(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> M:
        """
        Chuyển dict thành Model.

        Args:
            data: Dictionary từ Firestore.
            doc_id: Document ID.

        Returns:
            Pydantic model instance.
        """
        # Thêm document ID nếu model có field id
        if doc_id and "id" not in data:
            if (
                hasattr(self.model, "__fields__")
                and "id" in self.model.__fields__
            ):
                data["id"] = doc_id

        return self.model(**data)

    async def create_document(
        self, document: Union[Dict[str, Any], M], doc_id: Optional[str] = None
    ) -> str:
        """
        Tạo document mới trong Firestore.

        Args:
            document: Dictionary hoặc Model chứa dữ liệu.
            doc_id: ID của document (optional, Firestore sẽ tự tạo nếu không có).

        Returns:
            ID của document đã tạo.
        """
        try:
            # Chuyển Model thành dict nếu cần
            if isinstance(document, BaseModel):
                data = self._model_to_dict(document)
            else:
                data = dict(document)

            # Tạo document
            if doc_id:
                doc_ref = self.collection.document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = self.collection.add(data)[1]
                return doc_ref.id

        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {str(e)}")
            raise DatabaseException(detail=f"Lỗi khi tạo document: {str(e)}")

    async def get_document(self, doc_id: str) -> Optional[M]:
        """
        Lấy document từ Firestore theo ID.

        Args:
            doc_id: ID của document.

        Returns:
            Model instance nếu tìm thấy, None nếu không tìm thấy.
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return self._dict_to_model(doc.to_dict(), doc_id)

        except Exception as e:
            logger.error(
                f"Error getting document {doc_id} from {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi lấy document: {str(e)}")

    async def update_document(
        self, doc_id: str, document: Union[Dict[str, Any], M]
    ) -> M:
        """
        Cập nhật document trong Firestore.

        Args:
            doc_id: ID của document.
            document: Dictionary hoặc Model chứa dữ liệu cập nhật.

        Returns:
            Model instance sau khi cập nhật.
        """
        try:
            # Chuyển Model thành dict nếu cần
            if isinstance(document, BaseModel):
                data = self._model_to_dict(document)
            else:
                data = dict(document)
                data["updated_at"] = SERVER_TIMESTAMP

            # Cập nhật document
            doc_ref = self.collection.document(doc_id)

            # Kiểm tra document có tồn tại không
            if not doc_ref.get().exists:
                raise NotFoundException(detail=f"Document không tồn tại: {doc_id}")

            doc_ref.update(data)

            # Lấy document sau khi cập nhật
            updated_doc = doc_ref.get()
            return self._dict_to_model(updated_doc.to_dict(), doc_id)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating document {doc_id} in {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi cập nhật document: {str(e)}")

    async def delete_document(self, doc_id: str) -> bool:
        """
        Xóa document từ Firestore.

        Args:
            doc_id: ID của document.

        Returns:
            True nếu xóa thành công.
        """
        try:
            doc_ref = self.collection.document(doc_id)

            # Kiểm tra document có tồn tại không
            if not doc_ref.get().exists:
                raise NotFoundException(detail=f"Document không tồn tại: {doc_id}")

            doc_ref.delete()
            return True

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting document {doc_id} from {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi xóa document: {str(e)}")

    async def list_documents(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[M]:
        """
        Lấy danh sách documents từ Firestore.

        Args:
            limit: Số lượng documents tối đa.
            offset: Số lượng documents bỏ qua.
            order_by: Trường để sắp xếp.
            filters: Danh sách các điều kiện lọc.
                Format: [{"field": "name", "operator": "==", "value": "test"}]

        Returns:
            Danh sách Model instances.
        """
        try:
            query: Query = self.collection

            # Áp dụng filters
            if filters:
                for filter_condition in filters:
                    field = filter_condition.get("field")
                    operator = filter_condition.get("operator", "==")
                    value = filter_condition.get("value")

                    if field and value is not None:
                        query = query.where(field, operator, value)

            # Áp dụng order by
            if order_by:
                if order_by.startswith("-"):
                    # Descending order
                    query = query.order_by(order_by[1:], direction=Query.DESCENDING)
                else:
                    # Ascending order
                    query = query.order_by(order_by)

            # Áp dụng offset
            if offset:
                query = query.offset(offset)

            # Áp dụng limit
            if limit:
                query = query.limit(limit)

            # Thực hiện query
            docs = query.stream()

            # Chuyển kết quả thành models
            results = []
            for doc in docs:
                model = self._dict_to_model(doc.to_dict(), doc.id)
                results.append(model)

            return results

        except Exception as e:
            logger.error(
                f"Error listing documents from {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi lấy danh sách documents: {str(e)}")

    async def count_documents(
        self, filters: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Đếm số lượng documents trong collection.

        Args:
            filters: Danh sách các điều kiện lọc.

        Returns:
            Số lượng documents.
        """
        try:
            query: Query = self.collection

            # Áp dụng filters
            if filters:
                for filter_condition in filters:
                    field = filter_condition.get("field")
                    operator = filter_condition.get("operator", "==")
                    value = filter_condition.get("value")

                    if field and value is not None:
                        query = query.where(field, operator, value)

            # Đếm documents
            docs = list(query.stream())
            return len(docs)

        except Exception as e:
            logger.error(
                f"Error counting documents in {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi đếm documents: {str(e)}")

    async def batch_create(
        self, documents: List[Union[Dict[str, Any], M]]
    ) -> List[str]:
        """
        Tạo nhiều documents cùng lúc.

        Args:
            documents: Danh sách documents cần tạo.

        Returns:
            Danh sách IDs của documents đã tạo.
        """
        try:
            batch = self.client.batch()
            doc_ids = []

            for document in documents:
                # Chuyển Model thành dict nếu cần
                if isinstance(document, BaseModel):
                    data = self._model_to_dict(document)
                else:
                    data = dict(document)

                # Tạo document reference
                doc_ref = self.collection.document()
                batch.set(doc_ref, data)
                doc_ids.append(doc_ref.id)

            # Commit batch
            batch.commit()
            return doc_ids

        except Exception as e:
            logger.error(
                f"Error batch creating documents in {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(detail=f"Lỗi khi tạo hàng loạt documents: {str(e)}")

    async def batch_update(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Cập nhật nhiều documents cùng lúc.

        Args:
            updates: Danh sách updates với format:
                [{"doc_id": "...", "data": {...}}]

        Returns:
            True nếu thành công.
        """
        try:
            batch = self.client.batch()

            for update in updates:
                doc_id = update.get("doc_id")
                data = update.get("data", {})

                if not doc_id:
                    continue

                # Chuyển Model thành dict nếu cần
                if isinstance(data, BaseModel):
                    data = self._model_to_dict(data)
                else:
                    data = dict(data)
                    data["updated_at"] = SERVER_TIMESTAMP

                doc_ref = self.collection.document(doc_id)
                batch.update(doc_ref, data)

            # Commit batch
            batch.commit()
            return True

        except Exception as e:
            logger.error(
                f"Error batch updating documents in {self.collection_name}: {str(e)}"
            )
            raise DatabaseException(
                detail=f"Lỗi khi cập nhật hàng loạt documents: {str(e)}"
            )
