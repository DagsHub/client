import os
import pytest
from tests.dda.mock_api import MockApi


@pytest.fixture
def repouser():
    return "user"


@pytest.fixture
def reponame():
    return "repo"


@pytest.fixture
def repopath(repouser, reponame):
    return f"{repouser}/{reponame}"


@pytest.fixture
def current_revision(dagshub_repo):
    return dagshub_repo.api.heads.main.commit.hexsha


@pytest.fixture
def mock_api(dagshub_repo):
    with MockApi(
        git_repo=dagshub_repo, base_url="https://dagshub.com", assert_all_called=False
    ) as respx_mock:
        yield respx_mock


@pytest.fixture
def dagshub_repo(git_repo, repopath):
    cwd = os.getcwd()
    os.chdir(git_repo.workspace)
    repo = git_repo.api
    # Add remote
    repo.create_remote("origin", f"https://dagshub.com/{repopath}.git")
    # Create an initial commit
    filename = "test_git_file.txt"
    open(filename, "wb").close()
    repo.index.add([filename])
    repo.index.commit("initial commit")
    yield git_repo
    os.chdir(cwd)
