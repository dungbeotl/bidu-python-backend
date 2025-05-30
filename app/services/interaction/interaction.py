from app.services import BaseService
from app.db import firebase_db
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from .constant import TZ_ASIA_HCM, TrackingType, TableName, EventType
from app.utils import convert_to_timestamp
from app.constants import unknown, get_payment_method_name, E_PAYMENT_IDS
from app.db.repositories import OrderItemRepository, FeedbackRepository
from app.utils import to_timestamp
from app.constants import (
    PaymentMethodId,
    ShippingStatus,
    PaymentStatus,
)
from app.utils import ExportUtil, to_lower_strip
from app.core.exceptions import BadRequestException, DatabaseException
import logging
from google.cloud.firestore_v1.base_query import FieldFilter
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class InteractionService(BaseService[None]):
    """Service for interaction operations."""

    def __init__(self):
        super().__init__(None)

    async def get_interactions_for_personalize(self) -> List[Dict[str, Any]]:
        """Export interactions for Personalize."""
        processed_interactions = []

        print("Start export interactions for Personalize")
        # Interaction from Firebase for Personalize
        raw_interactions = await self._get_interactions_for_personalize()
        for raw_interaction in raw_interactions:
            # Process each raw interaction (có thể tạo nhiều record từ 1 raw)
            records = await self._process_interaction_for_personalize(raw_interaction)
            processed_interactions.extend(records)

        print("Start export buy product interactions for Personalize")
        # Interaction from Order Item for Personalize
        buy_product_interactions = await self._get_buy_product_interactions()
        processed_interactions.extend(buy_product_interactions)

        print("Start export feedback interactions for Personalize")
        # Interaction from Feedback for Personalize
        feedback_interactions = await self._get_feeback_interactions()
        processed_interactions.extend(feedback_interactions)

        print("End export feedback interactions for Personalize")
        return processed_interactions

    async def _export_to_format(
        self, data: List[Dict[str, Any]], format: str
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Helper method để export dữ liệu theo format, tránh dư thừa code.

        Args:
            data: Dữ liệu đã được xử lý
            format: Định dạng xuất (json, csv)

        Returns:
            StreamingResponse hoặc dict thông tin
        """
        # Kiểm tra nếu không có dữ liệu
        if not data:
            return {"success": False, "message": "Không có dữ liệu tương tác"}

        # Xử lý xuất theo định dạng
        if format.lower() == "json":
            return await ExportUtil()._export_dataset_to_json(data)
        elif format.lower() == "csv":
            return await ExportUtil()._export_dataset_to_csv(data)
        else:
            raise BadRequestException(detail=f"Định dạng {format} không được hỗ trợ")

    async def export_interactions_for_personalize(
        self, format: str = "json", personalize_format: str = "custom"
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """Export interactions for Personalize với support cho cả custom và ecommerce format."""
        try:
            # Get interactions dựa trên personalize_format
            if personalize_format == "ecommerce":
                processed_interactions = (
                    await self.get_interactions_for_personalize_ecommerce()
                )
            else:  # default to custom
                processed_interactions = await self.get_interactions_for_personalize()

            return await self._export_to_format(processed_interactions, format)
        except Exception as e:
            logger.error(f"Error exporting interactions for Personalize: {e}")
            raise DatabaseException(detail=f"Lỗi khi xuất dữ liệu tương tác: {e}")

    async def get_interactions_for_personalize_ecommerce(self) -> List[Dict[str, Any]]:
        """Export interactions for Personalize với format ecommerce đơn giản."""
        processed_interactions = []

        print("Start export interactions for Personalize ecommerce")
        # Interaction from Firebase for Personalize
        raw_interactions = await self._get_interactions_for_personalize()
        for raw_interaction in raw_interactions:
            # Process each raw interaction (có thể tạo nhiều record từ 1 raw)
            records = await self._process_interaction_for_personalize_ecommerce(
                raw_interaction
            )
            processed_interactions.extend(records)

        print("Start export buy product interactions for Personalize ecommerce")
        # Interaction from Order Item for Personalize
        buy_product_interactions = await self._get_buy_product_interactions_ecommerce()
        processed_interactions.extend(buy_product_interactions)

        print("Start export feedback interactions for Personalize ecommerce")
        # Interaction from Feedback for Personalize
        feedback_interactions = await self._get_feeback_interactions_ecommerce()
        processed_interactions.extend(feedback_interactions)

        print("End export feedback interactions for Personalize ecommerce")
        return processed_interactions

    async def export_interactions_for_personalize_ecommerce(
        self, format: str = "json"
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """Export interactions for Personalize với format ecommerce đơn giản."""
        try:
            # Get interactions for Personalize
            processed_interactions = (
                await self.get_interactions_for_personalize_ecommerce()
            )
            return await self._export_to_format(processed_interactions, format)
        except Exception as e:
            logger.error(f"Error exporting interactions for Personalize ecommerce: {e}")
            raise DatabaseException(
                detail=f"Lỗi khi xuất dữ liệu tương tác ecommerce: {e}"
            )

    # ******************************************************#
    # Interaction from Firebase for Personalize
    # Define: Interaction: view_product, add_product_to_favorite, add_cart
    # ******************************************************#

    async def _process_interaction_for_personalize(
        self, raw_interaction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process interactions for Personalize."""

        # Mapping EVENT_VALUE từ action_type
        event_value_mapping = {
            "view_product": 1,
            "add_product_to_favorite": 2,
            "add_cart": 2.5,
        }

        # Extract base data
        user_id = raw_interaction.get("actor_id", unknown)
        item_id = raw_interaction.get("target_id", unknown)
        event_type = raw_interaction.get("action_type", unknown)
        shop_id = raw_interaction.get("shop_id", unknown)
        event_value = event_value_mapping.get(event_type, 0)
        visited_ats = raw_interaction.get("visited_ats", [])

        # Nếu không có visited_ats, dùng created_at
        if not visited_ats:
            visited_ats = [raw_interaction.get("created_at")]

        # Tạo record cho mỗi timestamp trong visited_ats
        records = []
        for timestamp in visited_ats:
            if timestamp:  # Chỉ tạo record nếu có timestamp
                record = {
                    "ITEM_ID": item_id,
                    "USER_ID": user_id,
                    "EVENT_TYPE": event_type,
                    "TIMESTAMP": timestamp,
                    "SHOP_ID": shop_id,
                    "EVENT_VALUE": event_value,
                    "ORDER_VALUE": 0,
                    "BASKET_SIZE": 0,
                    "PAYMENT_METHOD": unknown,
                    "DELIVERY_LOCATION": unknown,
                }
                records.append(record)

        return records

    async def _get_interactions_for_personalize(
        self,
        action_types: Optional[List[str]] = None,
    ):
        """Get interactions for Personalize."""
        try:
            if not firebase_db.is_available():
                return []

            if action_types is None:
                action_types = [
                    TrackingType.VIEW_PRODUCT.value,
                    TrackingType.ADD_PRODUCT_TO_CART.value,
                    TrackingType.ADD_PRODUCT_TO_FAVORITE.value,
                ]

            # Build query
            query = self._build_tracking_query(action_types)

            # Execute query and return results
            return await self._execute_tracking_query_paginated(query)
        except Exception as e:
            raise e

    def _convert_timestamps_to_dates(
        self, from_timestamp: int, to_timestamp: int
    ) -> tuple:
        """Convert Unix timestamps to timezone-aware datetime objects."""

        # Convert from timestamp (start of day + 7 hours)
        start_date = datetime.fromtimestamp(from_timestamp, tz=TZ_ASIA_HCM)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date + timedelta(hours=7)

        # Convert to timestamp (end of day + 7 hours)
        end_date = datetime.fromtimestamp(to_timestamp, tz=TZ_ASIA_HCM)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        end_date = end_date + timedelta(hours=7)

        return start_date, end_date

    def _build_tracking_query(self, action_types: List[str]):
        """Build Firestore query for tracking activities."""

        return (
            firebase_db.firestore.collection(TableName.TRACKING_ACTIVITIES)
            .where(filter=FieldFilter("action_type", "in", action_types))
            .select(
                [
                    "actor_id",
                    "visited_ats",
                    "created_at",
                    "action_type",
                    "target_id",
                    "shop_id",
                    "target_type",
                ]
            )
        )

    def _handle_interaction_data(
        self, docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Handle interaction data."""

        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id

            # Convert created_at to timestamp if it's a datetime
            data["created_at"] = convert_to_timestamp(data.get("created_at"))
            data["visited_ats"] = convert_to_timestamp(data.get("visited_ats"))

            results.append(data)

        return results

    async def _execute_tracking_query_paginated(
        self, base_query, limit: int = None
    ) -> List[Dict[str, Any]]:
        """Execute tracking query with pagination to get all results."""

        all_results = []
        last_doc = None
        batch_size = 1000
        batch_count = 0

        while True:
            try:
                # Calculate batch size for this iteration
                remaining = (limit - len(all_results)) if limit else batch_size
                if remaining <= 0:
                    break
                current_batch_size = min(batch_size, remaining)

                # Build and execute query
                query = (
                    base_query.start_after(last_doc).limit(current_batch_size)
                    if last_doc
                    else base_query.limit(current_batch_size)
                )
                docs = list(query.stream())

                # Process documents
                if not docs:
                    break

                batch_results = self._handle_interaction_data(docs)
                all_results.extend(batch_results)

                last_doc = docs[-1]
                batch_count += 1

                # Stop if we got less than requested (end of data)
                if len(docs) < current_batch_size:
                    break

            except Exception as e:
                break

        return (
            all_results[:limit] if limit and len(all_results) > limit else all_results
        )

    # ******************************************************#
    # Interaction from Order Item for Personalize
    # Define: Interaction: buy_product
    # ******************************************************#

    async def _get_buy_product_interactions(self):
        """Get buy product interactions."""
        order_item_repo = OrderItemRepository()
        order_items = await order_item_repo.get_all_order_items()
        personalize_interactions = []
        for order_item in order_items:
            personalize_interaction = self._transform_order_item_to_personalize(
                order_item
            )
            if not personalize_interaction:
                continue
            personalize_interactions.append(personalize_interaction)
        return personalize_interactions

    def _transform_order_item_to_personalize(
        self, order_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform một OrderItem thành format cho AWS Personalize.

        Args:
            order_item: Dictionary chứa dữ liệu OrderItem

        Returns:
            Dictionary với format cho AWS Personalize
        """

        try:
            # Lấy các giá trị cần thiết với safe access
            orders = order_item.get("order", [])
            if not orders or len(orders) == 0:
                print(f"Không tìm thấy order cho orderitem: {order_item.get('_id')}")
                return None

            order = orders[0]

            item_id = order_item.get("product_id", unknown)
            quantity = order_item.get("quantity", 1)
            created_at = order_item.get("created_at")

            shop_id = order.get("shop_id", unknown)
            user_id = order.get("user_id", unknown)
            payment_method_id = order.get("payment_method_id", unknown)

            # Tính ORDER_VALUE
            order_value = 0
            if "variant" in order_item and order_item["variant"]:
                order_value = order_item["variant"].get("before_sale_price", 0)
            elif "product" in order_item and order_item["product"]:
                order_value = order_item["product"].get("before_sale_price", 0)

            # Lấy delivery location
            delivery_location = unknown
            buyer_address = order.get("address", {})

            # Đơn hàng: địa chỉ có giá trị VN hoặc "" -> lấy tỉnh thành
            if (
                buyer_address.get("country") == "VN"
                or buyer_address.get("country") == ""
            ):  # noqa: E501
                delivery_location = buyer_address.get("state", {}).get("name", unknown)
            elif buyer_address.get("country") == "SG":
                delivery_location = "singapore"
            else:
                delivery_location = unknown

            # (
            #     order.get("address", {}).get("state", {}).get("name", unknown)
            # )

            # Tạo timestamp
            timestamp = to_timestamp(created_at)
            event_value = self._calculate_event_value(order)

            personalize_data = {
                "USER_ID": str(user_id),
                "ITEM_ID": str(item_id),
                "EVENT_TYPE": EventType.PURCHASE.value,
                "TIMESTAMP": timestamp,
                "SHOP_ID": str(shop_id),
                "EVENT_VALUE": event_value,
                "ORDER_VALUE": order_value,
                "BASKET_SIZE": int(quantity),
                "DELIVERY_LOCATION": to_lower_strip(delivery_location),
                "PAYMENT_METHOD": get_payment_method_name(payment_method_id),
            }

            return personalize_data
        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            logger.error(f"Error getting buy product interactions: {e}")
            logger.error(f"Full traceback:\n{error_traceback}")
            raise e

    def _calculate_event_value(cls, order: Dict[str, Any]) -> float:
        """
        Calculate EVENT_VALUE based on payment_method_id, shipping_status, and payment_status.

        Args:
            order: Order dictionary containing payment and shipping info

        Returns:
            EVENT_VALUE as float
        """
        if not order:
            return 0

        payment_method_id = order.get("payment_method_id", "")
        shipping_status = order.get("shipping_status", "").lower()
        payment_status = order.get("payment_status", "").lower()

        # Determine if COD or e-payment
        is_cod = payment_method_id == PaymentMethodId.CASH_ID.value
        is_epayment = payment_method_id in E_PAYMENT_IDS

        if is_cod:
            return cls._calculate_cod_event_value(shipping_status, payment_status)
        elif is_epayment:
            return cls._calculate_epayment_event_value(shipping_status, payment_status)
        else:
            # Unknown payment method, default
            return 0.5

    def _calculate_cod_event_value(
        self, shipping_status: str, payment_status: str
    ) -> float:
        """Calculate EVENT_VALUE for COD orders."""

        # shipping_status: [pending] && payment_status: 'pending' => 3
        if (
            shipping_status == ShippingStatus.PENDING.value
            and payment_status == PaymentStatus.PENDING.value
        ):
            return 3.0

        # shipping_status: [wait_to_pick, shipping, shipped] && payment_status: [paid, pending] => 5
        if shipping_status in [
            ShippingStatus.WAIT_TO_PICK.value,
            ShippingStatus.SHIPPING.value,
            ShippingStatus.SHIPPED.value,
        ] and payment_status in [PaymentStatus.PAID.value, PaymentStatus.PENDING.value]:
            return 5.0

        # shipping_status: [canceling, canceled] && payment_status: [pending] => 0.5
        if (
            shipping_status
            in [
                ShippingStatus.CANCELING.value,
                ShippingStatus.CANCELED.value,
            ]
            and payment_status == PaymentStatus.PENDING.value
        ):
            return 0.5

        # shipping_status: [canceling, canceled] && payment_status: [paid] => 1.5
        if (
            shipping_status
            in [
                ShippingStatus.CANCELING.value,
                ShippingStatus.CANCELED.value,
            ]
            and payment_status == PaymentStatus.PAID.value
        ):
            return 1.5

        # shipping_status: [return, returning] && payment_status [paid, pending] => 1.5
        if shipping_status in [
            ShippingStatus.RETURN.value,
            ShippingStatus.RETURNING.value,
        ] and payment_status in [PaymentStatus.PAID.value, PaymentStatus.PENDING.value]:
            return 1.5

    def _calculate_epayment_event_value(
        self, shipping_status: str, payment_status: str
    ) -> float:
        """Calculate EVENT_VALUE for e-payment orders."""

        # shipping_status: [wait_to_pick, shipping, shipped] && payment_status: [paid] => 5
        if (
            shipping_status
            in [
                ShippingStatus.WAIT_TO_PICK.value,
                ShippingStatus.SHIPPING.value,
                ShippingStatus.SHIPPED.value,
            ]
            and payment_status == PaymentStatus.PAID.value
        ):
            return 5.0

        # shipping_status: [pending] && payment_status: [pending] => 1
        if (
            shipping_status == ShippingStatus.PENDING.value
            and payment_status == PaymentStatus.PENDING.value
        ):
            return 1.0

        # shipping_status: [canceling, canceled] && payment_status: [paid] => 2
        if (
            shipping_status
            in [
                ShippingStatus.CANCELING.value,
                ShippingStatus.CANCELED.value,
            ]
            and payment_status == PaymentStatus.PAID.value
        ):
            return 2.0

        # shipping_status: [return, returning] && payment_status [paid] => 1.5
        if (
            shipping_status
            in [
                ShippingStatus.RETURN.value,
                ShippingStatus.RETURNING.value,
            ]
            and payment_status == PaymentStatus.PAID.value
        ):
            return 1.5

    # ******************************************************#
    # Interaction from Feedback for Personalize
    # Define: Interaction: review
    # ******************************************************#

    async def _get_feeback_interactions(self):
        """Get review interactions."""
        feedback_repo = FeedbackRepository()
        feedbacks = await feedback_repo.get_all_feedback(target_type="Product")
        personalize_interactions = []
        for feedback in feedbacks:
            personalize_interaction = self._transform_feedback_to_personalize(feedback)

            if not personalize_interaction:
                continue
            personalize_interactions.append(personalize_interaction)
        return personalize_interactions

    def _transform_feedback_to_personalize(
        self, feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform feedback to personalize."""

        return {
            "USER_ID": feedback.get("user_id", unknown),
            "ITEM_ID": feedback.get("target_id", unknown),
            "EVENT_TYPE": EventType.REVIEW.value,
            "TIMESTAMP": to_timestamp(feedback.get("created_at", unknown)),
            "SHOP_ID": feedback.get("shop_id", unknown),
            "EVENT_VALUE": feedback.get("vote_star", 0),
            "ORDER_VALUE": 0,
            "BASKET_SIZE": 0,
            "PAYMENT_METHOD": unknown,
            "DELIVERY_LOCATION": unknown,
        }

    def _convert_event_type_to_personalize(self, event_type: str) -> str:
        """Convert event type to personalize."""
        if event_type == TrackingType.VIEW_PRODUCT.value:
            return EventType.VIEW.value
        elif event_type == TrackingType.ADD_PRODUCT_TO_CART.value:
            return EventType.ADD_TO_CART.value
        elif event_type == TrackingType.BUY_PRODUCT.value:
            return EventType.PURCHASE.value
        elif event_type == TrackingType.ADD_PRODUCT_TO_FAVORITE.value:
            return EventType.FAVORITE.value
        return EventType.REVIEW.value

    async def _process_interaction_for_personalize_ecommerce(
        self, raw_interaction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process interactions for Personalize với format ecommerce đơn giản."""

        # Mapping EVENT_VALUE từ action_type
        event_value_mapping = {
            EventType.VIEW.value: 1,
            EventType.FAVORITE.value: 2,
            EventType.ADD_TO_CART.value: 2.5,
        }

        # Extract base data
        user_id = raw_interaction.get("actor_id", unknown)
        item_id = raw_interaction.get("target_id", unknown)

        tracking_type = raw_interaction.get("action_type", unknown)
        event_type = self._convert_event_type_to_personalize(tracking_type)

        event_value = event_value_mapping.get(event_type, 0)
        visited_ats = raw_interaction.get("visited_ats", [])

        # Nếu không có visited_ats, dùng created_at
        if not visited_ats:
            visited_ats = [raw_interaction.get("created_at")]

        # Tạo record cho mỗi timestamp trong visited_ats với format ecommerce đơn giản
        records = []
        for timestamp in visited_ats:
            if timestamp:  # Chỉ tạo record nếu có timestamp
                record = {
                    "USER_ID": user_id,
                    "ITEM_ID": item_id,
                    "TIMESTAMP": timestamp,
                    "EVENT_TYPE": event_type,
                    "EVENT_VALUE": event_value,
                }
                records.append(record)

        return records

    async def _get_buy_product_interactions_ecommerce(self):
        """Get buy product interactions với format ecommerce đơn giản."""
        order_item_repo = OrderItemRepository()
        order_items = await order_item_repo.get_all_order_items()
        personalize_interactions = []
        for order_item in order_items:
            personalize_interaction = (
                self._transform_order_item_to_personalize_ecommerce(order_item)
            )
            if not personalize_interaction:
                continue
            personalize_interactions.append(personalize_interaction)
        return personalize_interactions

    def _transform_order_item_to_personalize_ecommerce(
        self, order_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform một OrderItem thành format cho AWS Personalize với format ecommerce đơn giản.

        Args:
            order_item: Dictionary chứa dữ liệu OrderItem

        Returns:
            Dictionary với format ecommerce đơn giản cho AWS Personalize
        """

        try:
            # Lấy các giá trị cần thiết với safe access
            orders = order_item.get("order", [])
            if not orders or len(orders) == 0:
                print(f"Không tìm thấy order cho orderitem: {order_item.get('_id')}")
                return None

            order = orders[0]

            item_id = order_item.get("product_id", unknown)
            created_at = order_item.get("created_at")
            user_id = order.get("user_id", unknown)

            # Tạo timestamp
            timestamp = to_timestamp(created_at)

            # Tính EVENT_VALUE cho buy product
            event_value = self._calculate_event_value(order)

            personalize_data = {
                "USER_ID": str(user_id),
                "ITEM_ID": str(item_id),
                "TIMESTAMP": timestamp,
                "EVENT_TYPE": EventType.PURCHASE.value,
                "EVENT_VALUE": event_value,
            }

            return personalize_data
        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            logger.error(f"Error getting buy product interactions ecommerce: {e}")
            logger.error(f"Full traceback:\n{error_traceback}")
            raise e

    async def _get_feeback_interactions_ecommerce(self):
        """Get review interactions với format ecommerce đơn giản."""
        feedback_repo = FeedbackRepository()
        feedbacks = await feedback_repo.get_all_feedback(target_type="Product")
        personalize_interactions = []
        for feedback in feedbacks:
            personalize_interaction = self._transform_feedback_to_personalize_ecommerce(
                feedback
            )

            if not personalize_interaction:
                continue
            personalize_interactions.append(personalize_interaction)
        return personalize_interactions

    def _transform_feedback_to_personalize_ecommerce(
        self, feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform feedback to personalize với format ecommerce đơn giản."""

        return {
            "USER_ID": feedback.get("user_id", unknown),
            "ITEM_ID": feedback.get("target_id", unknown),
            "TIMESTAMP": to_timestamp(feedback.get("created_at", unknown)),
            "EVENT_TYPE": EventType.REVIEW.value,
            "EVENT_VALUE": feedback.get("vote_star", 0),
        }
