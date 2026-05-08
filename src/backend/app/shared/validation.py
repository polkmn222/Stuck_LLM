from app.shared.datetime_utils import parse_aware_datetime


def require_timezone_datetime(value: str) -> str:
    try:
        parse_aware_datetime(
            value,
            error_message="datetime must be a valid ISO 8601 value",
            timezone_error_message="datetime must include a timezone offset",
        )
    except ValueError as error:
        raise ValueError(str(error)) from error
    return value
