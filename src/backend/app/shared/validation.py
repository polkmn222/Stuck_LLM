from datetime import datetime


def require_timezone_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("datetime must be a valid ISO 8601 value") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("datetime must include a timezone offset")
    return value
