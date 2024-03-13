from pathlib import Path
from unittest.mock import patch

import pytest

from dagshub.streaming import DagsHubFilesystem, uninstall_hooks
from tests.mocks.repo_api import MockRepoAPI


@pytest.fixture
def username():
    return "user"


@pytest.fixture
def repo_1_name():
    return "repo1"


@pytest.fixture
def repo_2_name():
    return "repo2"


@pytest.fixture
def repo_1(username, repo_1_name) -> MockRepoAPI:
    repo = MockRepoAPI(f"{username}/{repo_1_name}")
    repo.add_repo_file("a/b.txt", b"content repo 1")
    return repo


@pytest.fixture
def repo_2(username, repo_2_name) -> MockRepoAPI:
    repo = MockRepoAPI(f"{username}/{repo_2_name}")
    repo.add_repo_file("a/b.txt", b"content repo 2")
    return repo


def mock_repo_api_patch(repo_api: MockRepoAPI):
    def mocked(_self: DagsHubFilesystem, _path):
        return repo_api

    return mocked


def generate_mock_fs(repo_api: MockRepoAPI, file_dir: Path) -> DagsHubFilesystem:
    with patch("dagshub.streaming.DagsHubFilesystem._generate_repo_api", mock_repo_api_patch(repo_api)):
        fs = DagsHubFilesystem(project_root=file_dir, repo_url="https://localhost.invalid")
        return fs


def test_mock_fs_works(repo_1, tmp_path):
    fs = generate_mock_fs(repo_1, tmp_path)
    assert fs.open(tmp_path / "a/b.txt", "rb").read() == b"content repo 1"
    pass


def test_two_mock_fs(repo_1, repo_2, tmp_path):
    path1 = tmp_path / "repo1"
    path2 = tmp_path / "repo2"
    fs1 = generate_mock_fs(repo_1, path1)
    fs2 = generate_mock_fs(repo_2, path2)
    assert fs1.open(path1 / "a/b.txt", "rb").read() == b"content repo 1"
    assert fs2.open(path2 / "a/b.txt", "rb").read() == b"content repo 2"


def test_install_hooks_two_fs(repo_1, repo_2, tmp_path):
    path1 = tmp_path / "repo1"
    path2 = tmp_path / "repo2"
    fs1 = generate_mock_fs(repo_1, path1)
    fs2 = generate_mock_fs(repo_2, path2)

    try:
        fs1.install_hooks()
        fs2.install_hooks()

        assert open(path1 / "a/b.txt", "rb").read() == b"content repo 1"
        assert open(path2 / "a/b.txt", "rb").read() == b"content repo 2"
    finally:
        uninstall_hooks()
