from typing import List, Dict, Any


def to_hashmap(
    data: List[Dict[str, Any]], key: str = "id", skip_missing: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    Safe version với error handling.

    Args:
        data: List of data dictionaries
        key: Field name to use as hashmap key
        skip_missing: Skip items without the key (True) or raise error (False)

    Returns:
        Dictionary mapping key -> data
    """
    hashmap = {}

    for item in data:
        if key in item:
            hashmap[item[key]] = item
        elif not skip_missing:
            raise KeyError(f"Key '{key}' not found in item: {item}")

    return hashmap
