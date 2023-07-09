import pytest

from dagshub.upload import Repo
from tests.dda.mock_api import MockApi


@pytest.fixture
def upload_repo(repouser: str, reponame: str, mock_api: MockApi) -> Repo:
    mock_api.enable_uploads()
    repo = Repo(repouser, reponame)
    yield repo
