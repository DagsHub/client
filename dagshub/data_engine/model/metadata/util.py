import datetime
from gql.transport import exceptions as gql_transport_exceptions
from requests import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout
from typing import Optional

from dagshub.data_engine.model.errors import DataEngineGqlError

TransportServerError = gql_transport_exceptions.TransportServerError
# Some supported gql versions (e.g. 3.4.x) do not expose this symbol.
# Fallback to an empty tuple so isinstance(...) still works without broad try/except imports.
TransportConnectionFailed = getattr(gql_transport_exceptions, "TransportConnectionFailed", tuple())


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
    if isinstance(exc, DataEngineGqlError) and isinstance(exc.original_exception, Exception):
        return is_retryable_metadata_upload_error(exc.original_exception)

    return isinstance(
        exc,
        (
            TransportServerError,
            TransportConnectionFailed,
            TimeoutError,
            ConnectionError,
            RequestsConnectionError,
            RequestsTimeout,
        ),
    )
