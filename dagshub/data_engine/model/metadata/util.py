import base64
import datetime
import gzip
from typing import Optional


def wrap_bytes(val: bytes) -> str:
    """
    Handles bytes values for uploading metadata
    The process is gzip -> base64

    :meta private:
    """
    compressed = gzip.compress(val)
    return base64.b64encode(compressed).decode("utf-8")


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
