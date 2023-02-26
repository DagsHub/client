import pytest

from dagshub.upload import Repo


@pytest.fixture
def upload_repo(repouser, reponame, mock_api):
    repo = Repo(repouser, reponame)
    yield repo
