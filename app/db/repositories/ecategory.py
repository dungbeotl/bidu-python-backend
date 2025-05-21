from typing import Dict, List, Optional, Any
from datetime import datetime
from copy import deepcopy

from app.db.repositories import BaseRepository
from app.models import ECategory
from app.utils import convert_mongo_document
from app.constants import ECATEGORIES_IDS


class ECategoryRepository(BaseRepository[ECategory]):
    """Repository cho collection products sử dụng Beanie."""

    def __init__(self):
        """Khởi tạo Product Repository."""
        super().__init__(ECategory)

    async def get_all_categories(self) -> List[ECategory]:
        """Lấy tất cả danh mục sản phẩm."""
        return await self.find_by_ids(ECATEGORIES_IDS)

    async def get_tree_categories(self) -> List[Dict[str, Any]]:
        """Lấy tất cả danh mục sản phẩm dạng cây."""
        categories_raw = await self.get_all_categories()
        categories = convert_mongo_document(categories_raw)
        return self.get_tree_all(categories)

    def build_tree(
        self,
        data: List[Dict[str, Any]],
        parent_id: Optional[str],
        res: List[Dict[str, Any]],
        level: int,
    ):
        for item in data:
            if item.get("parent_id") == parent_id:
                item["level"] = level
                item["childs"] = []
                res.append(item)
                self.build_tree(data, item["id"], item["childs"], level + 1)

    def get_tree_all(
        self, data: List[Dict[str, Any]], root_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tạo cây danh mục từ danh sách danh mục phẳng (không cần localize).
        :param data: Danh sách danh mục (list các dict).
        :param root_category: ID danh mục cha (mặc định là None).
        :return: Cây danh mục.
        """
        cloned_data = deepcopy(data)

        for item in cloned_data:
            item["childs"] = []

        tree = []
        self.build_tree(cloned_data, root_category, tree, level=1)
        return tree

    def flatten_tree(self, tree, level=1, parent_id=None, result=None):
        if result is None:
            result = []

        for node in tree:
            node_id = node.get("id")
            result.append(
                {
                    "id": node_id,
                    "name": node.get("name"),
                    "level": level,
                    "parent_id": parent_id,
                }
            )

            # Đệ quy nếu có childs
            childs = node.get("childs", [])
            if isinstance(childs, list) and childs:
                self.flatten_tree(childs, level + 1, node_id, result)

        return result
