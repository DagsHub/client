import pytest

from dagshub.upload import Repo


@pytest.fixture
def upload_repo(repouser, reponame, mock_api):
    mock_api.enable_uploads()
    repo = Repo(repouser, reponame)
    yield repo
