import httpx

from dagshub.upload.errors import determine_error, UpdateNotAllowedError


def test_determine_error():
    resp = httpx.Response(400, content='{"error": "missing last_commit", "details": "file exist"}')
    err = determine_error(resp)
    assert isinstance(err, UpdateNotAllowedError)

