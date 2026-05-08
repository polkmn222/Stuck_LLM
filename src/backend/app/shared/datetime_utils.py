from datetime import datetime
from typing import Any, Optional


def parse_aware_datetime(
    value: str,
    *,
    error_message: str = "datetime must be a valid ISO 8601 value",
    timezone_error_message: str = "datetime must include a timezone offset",
) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(error_message) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(timezone_error_message)
    return parsed


def parse_optional_aware_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed
