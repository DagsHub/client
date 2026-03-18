import datetime
from typing import Optional

from gql.transport.exceptions import TransportError, TransportQueryError
from requests import ConnectionError as RequestsConnectionError
from requests import Timeout as RequestsTimeout

from dagshub.data_engine.model.errors import DataEngineGqlError


def _get_datetime_utc_offset(t: datetime.datetime) -> Optional[str]:
    """
    return a timezone offset in the form of "+03:00" or "-03:00"
    """

    if t.tzinfo is None:
        return None

    offset = t.utcoffset()
    if offset is None:
        return None

    # Format the offset as a string
    offset_hours = int(offset.total_seconds() // 3600)
    offset_minutes = int((offset.total_seconds() % 3600) // 60)
    offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
    return offset_str


def is_retryable_metadata_upload_error(exc: Exception) -> bool:
    if isinstance(exc, DataEngineGqlError):
        return is_retryable_metadata_upload_error(exc.original_exception)

    return (isinstance(exc, TransportError) and not isinstance(exc, TransportQueryError)) or isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            RequestsConnectionError,
            RequestsTimeout,
        ),
    )
