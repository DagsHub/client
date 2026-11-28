from email import policy
from email.parser import BytesParser
from io import BytesIO, RawIOBase
from types import SimpleNamespace

import httpx
import pytest
from tenacity import RetryError

from dagshub.upload import wrapper
from dagshub.upload.errors import InternalServerErrorError, PathConflictError


class NonSeekable(RawIOBase):
    def __init__(self, data):
        super().__init__()
        self.stream = BytesIO(data)

    def readable(self):
        return True

    def read(self, size=-1):
        return self.stream.read(size)


@pytest.fixture
def upload(monkeypatch):
    def make_upload(statuses):
        contents = []

        def handle(request):
            content_type = request.headers["Content-Type"].encode("ascii")
            message = BytesParser(policy=policy.default).parsebytes(
                b"Content-Type: " + content_type + b"\r\n\r\n" + request.read()
            )
            contents.append({
                part.get_filename(): part.get_payload(decode=True)
                for part in message.iter_parts()
                if part.get_filename() is not None
            })
            status = statuses[len(contents) - 1]
            if status == 200:
                return httpx.Response(status, headers={"ETag": "new-revision"})
            error = {500: "server error", 409: "path conflict"}[status]
            return httpx.Response(status, json={"error": error, "details": "test upload"})

        client = httpx.Client(transport=httpx.MockTransport(handle), trust_env=False)
        clients.append(client)
        monkeypatch.setattr(wrapper, "s", client)
        monkeypatch.setattr(wrapper.Repo.upload_files.retry, "sleep", lambda seconds: None)
        repo = wrapper.Repo("owner", "repo", token="test-token", branch="main")
        repo._api = SimpleNamespace(is_mirror=False, last_commit_sha=lambda branch: "base-revision")
        return repo, contents

    clients = []
    yield make_upload
    for client in clients:
        client.close()


def test_upload_retries_replayable_files(upload, tmp_path):
    repo, contents = upload([500, 200])
    path = tmp_path / "checkpoint.bin"
    path.write_bytes(b"training checkpoint")
    with path.open("rb") as file:
        repo.upload_files([("checkpoint.bin", file), ("manifest.json", b"{}")], quiet=True)

    payload = {"checkpoint.bin": b"training checkpoint", "manifest.json": b"{}"}
    assert contents == [payload, payload]
    assert repo._last_upload_had_changes


@pytest.mark.parametrize("use_keyword", [False, True])
def test_upload_does_not_retry_a_consumed_stream(upload, use_keyword):
    repo, contents = upload([500, 200])
    files = [("manifest.json", BytesIO(b"{}")), ("dataset.jsonl", NonSeekable(b"training data"))]
    with pytest.raises(InternalServerErrorError):
        if use_keyword:
            repo.upload_files(files=files, quiet=True)
        else:
            repo.upload_files(files, quiet=True)

    assert contents == [{"manifest.json": b"{}", "dataset.jsonl": b"training data"}]
    assert not repo._last_upload_had_changes


def test_upload_allows_a_stream_when_first_attempt_succeeds(upload):
    repo, contents = upload([200])
    repo.upload_files([("dataset.jsonl", NonSeekable(b"training data"))], quiet=True)

    assert contents == [{"dataset.jsonl": b"training data"}]


def test_upload_does_not_retry_a_conflict(upload):
    repo, contents = upload([409])
    with pytest.raises(PathConflictError):
        repo.upload_files([("dataset.jsonl", BytesIO(b"training data"))], quiet=True)

    assert contents == [{"dataset.jsonl": b"training data"}]


def test_upload_retains_the_existing_retry_limit(upload):
    repo, contents = upload([500] * 5)
    with pytest.raises(RetryError):
        repo.upload_files([("dataset.jsonl", BytesIO(b"training data"))], quiet=True)

    assert contents == [{"dataset.jsonl": b"training data"}] * 5
