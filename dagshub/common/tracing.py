import secrets


def _generate_non_zero_hex(byte_count: int) -> str:
    """
    Generate a non-zero hex string of the given byte length.

    Per W3C Trace Context, trace-id and parent-id MUST NOT be all zeros.
    """
    while True:
        value = secrets.token_hex(byte_count)
        if int(value, 16) != 0:
            return value


def build_traceparent() -> str:
    """
    Build a W3C Trace Context traceparent header value.

    Format: version(2)-trace-id(32)-parent-id(16)-flags(2)
    """
    version = "00"
    trace_id = _generate_non_zero_hex(16)
    parent_id = _generate_non_zero_hex(8)
    flags = "01"  # sampled
    return f"{version}-{trace_id}-{parent_id}-{flags}"
