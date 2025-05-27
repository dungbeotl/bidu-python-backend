from datetime import datetime
from typing import Union, Optional, Any


def to_timestamp(date_value: Union[str, datetime, None]) -> Optional[int]:
    """
    Chuyển đổi datetime string hoặc datetime object sang timestamp

    Args:
        date_value: Giá trị thời gian (string hoặc datetime object)

    Returns:
        int: Timestamp (seconds since epoch) hoặc None nếu không parse được
    """
    if not date_value:
        return None

    try:
        if isinstance(date_value, str):
            # Parse ISO format string trực tiếp
            dt = datetime.fromisoformat(date_value)
            return int(dt.timestamp())
        elif isinstance(date_value, datetime):
            return int(date_value.timestamp())
    except (ValueError, AttributeError) as e:
        print(f"Error parsing timestamp {date_value}: {e}")

    return None


def convert_to_timestamp(value: Any) -> Any:
    """
    Convert datetime hoặc string sang timestamp, hỗ trợ cả single value và list

    Args:
        value: Có thể là datetime, string, list, hoặc bất kỳ giá trị nào

    Returns:
        Timestamp (int) hoặc list timestamps, hoặc giá trị gốc nếu không convert được
    """
    if isinstance(value, datetime):
        return int(value.timestamp())

    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return int(dt.timestamp())
        except ValueError:
            return value  # Trả về giá trị gốc nếu không parse được

    elif isinstance(value, list):
        converted = []
        for item in value:
            converted.append(convert_to_timestamp(item))  # Recursive call
        return converted

    else:
        return value  # Trả về giá trị gốc cho các type khác
