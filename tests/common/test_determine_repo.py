import os
import urllib.parse
import uuid
from typing import Generator, TypeVar
import respx

import pytest
import pytest_git

from dagshub.common.determine_repo import determine_repo, parse_dagshub_remote
import dagshub.common.config
from dagshub.common.errors import DagsHubRepoNotFoundError
from tests.dda.test_tokens import valid_token_side_effect
from tests.util import remember_cwd

T = TypeVar("T")

YieldFixture = Generator[T, None, None]


@pytest.fixture
def repo_name() -> str:
    return f"user/repo-{uuid.uuid4()}"


@pytest.fixture(
    params=[
        "https://dagshub.com",
        "https://internal.example.com",
        "https://somewhere.else:8080",
        "https://somewhere.else:8080/prefix",
    ]
)
def dagshub_host(request) -> YieldFixture[str]:
    host = request.param
    old_value = dagshub.common.config.host
    dagshub.common.config.host = host
    yield host
    dagshub.common.config.host = old_value


@pytest.fixture(params=[True, False])
def is_dagshub_origin(request) -> bool:
    return request.param


@pytest.fixture(params=[True, False])
def has_auth(request) -> bool:
    return request.param


@pytest.fixture
def dagshub_repo(
    git_repo: pytest_git.GitRepo, dagshub_host, is_dagshub_origin, has_auth, repo_name
) -> pytest_git.GitRepo:
    parsed_url = urllib.parse.urlparse(dagshub_host)
    if has_auth:
        remote_url = f"{parsed_url.scheme}://user:password@{parsed_url.hostname}{parsed_url.path}/{repo_name}.git"
    else:
        remote_url = f"{dagshub_host}/{repo_name}.git"
    other_remote = f"https://other-git-hosting.com/{repo_name}.git"

    repo = git_repo.api
    if is_dagshub_origin:
        repo.create_remote("origin", remote_url)
    else:
        repo.create_remote("origin", other_remote)
        repo.create_remote("dagshub", remote_url)

    (git_repo.workspace / "subdir").mkdir()
    with remember_cwd():
        os.chdir(git_repo.workspace)
        yield git_repo


@pytest.fixture
def repo_with_no_dagshub_remote(git_repo, repo_name) -> pytest_git.GitRepo:
    repo = git_repo.api
    other_remote = f"https://other-git-hosting.com/{repo_name}.git"
    repo.create_remote("origin", other_remote)

    with remember_cwd():
        os.chdir(git_repo.workspace)
        yield git_repo


def test_in_repo_root(dagshub_host, dagshub_repo, repo_name):
    _test_determine_repo(dagshub_host, dagshub_repo, repo_name)


def test_in_folder(dagshub_host, dagshub_repo, repo_name):
    os.chdir("subdir")
    _test_determine_repo(dagshub_host, dagshub_repo, repo_name)


def _test_determine_repo(dagshub_host: str, dagshub_repo: pytest_git.GitRepo, repo_name: str):
    with respx.mock(base_url=dagshub_host) as mock_router:
        mock_router.get("api/v1/user").mock(side_effect=valid_token_side_effect)
        res, branch = determine_repo()
        assert res.full_name == repo_name
        assert res.host == dagshub_host


def test_cant_find_repo(dagshub_host, repo_with_no_dagshub_remote):
    with pytest.raises(DagsHubRepoNotFoundError):
        _, _ = determine_repo()


def test_cant_find_repo_when_theres_no_repo(tmp_path):
    with remember_cwd():
        os.chdir(tmp_path)
        with pytest.raises(DagsHubRepoNotFoundError):
            _, _ = determine_repo()


@pytest.mark.parametrize(
    "url, host, expected",
    [
        ("https://dagshub.com/user/repo.git", "https://dagshub.com", "user/repo"),
        ("https://dagshub.com/user/repo", "https://dagshub.com", None),
        ("https://dagshub.com/random/prefix/user/repo", "https://dagshub.com", None),
        ("https://dagshub.com/docs", "https://dagshub.com", None),
        ("https://example.com/user/repo.git", "https://example.com", "user/repo"),
        ("https://example.com/user/repo.git", "https://dagshub.com", None),
        ("https://example.com/prefix/user/repo.git", "https://example.com/prefix", "user/repo"),
        ("https://user:password@dagshub.com/user/repo.git", "https://dagshub.com", "user/repo"),
        ("https://token:@dagshub.com/user/repo.git", "https://dagshub.com", "user/repo"),
    ],
)
def test_parse_dagshub_remote(url, host, expected):
    actual = parse_dagshub_remote(urllib.parse.urlparse(url), urllib.parse.urlparse(host))
    assert expected == actual
