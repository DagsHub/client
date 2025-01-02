import unittest.mock
from typing import List, Tuple

import pytest

from dagshub.upload import Repo
from tests.dda.mock_api import MockApi


@pytest.fixture
def upload_repo(repouser: str, reponame: str, mock_api: MockApi) -> Repo:
    mock_api.enable_uploads()
    repo = Repo(repouser, reponame)
    yield repo


class MockS3Client(unittest.mock.Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uploaded_files: List[Tuple[str, str]] = []

    def upload_file(self, *args):
        path = f"{args[1]}/{args[2]}"
        self.uploaded_files.append((path, args[0]))


@pytest.fixture()
def mock_s3_client():
    return MockS3Client()


@pytest.fixture
def mock_s3(monkeypatch, mock_s3_client):
    def get_client(*args, **kwargs):
        return mock_s3_client

    # Need to monkeypatch in the file that is importing, not the original function that's being imported
    monkeypatch.setattr("dagshub.upload.wrapper.get_repo_bucket_client", get_client)

    return mock_s3_client
