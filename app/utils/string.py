def to_lower_strip(value: str | None) -> str | None:
    if value is None:
        return None
    return value.lower().strip()
