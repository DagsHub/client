import base64
import gzip


def wrap_bytes(val: bytes) -> str:
    """
    Handles bytes values for uploading metadata
    The process is gzip -> base64

    :meta private:
    """
    compressed = gzip.compress(val)
    return base64.b64encode(compressed).decode("utf-8")
