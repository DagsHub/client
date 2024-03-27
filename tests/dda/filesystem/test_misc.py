import os.path
import secrets
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dagshub.streaming import DagsHubFilesystem
from dagshub.streaming.dataclasses import DagshubPath


@pytest.mark.parametrize(
    "path,expected",
    [
        ("regular/path/in/repo", False),
        (".", False),
        (".git/", True),
        (".git/and/then/some", True),
        (".dvc/", True),
        (".dvc/and/then/some", True),
        ("repo/file.dvc/", False),
        ("repo/file.git/", False),
        ("venv/lib/site-packages/some-package", True),
    ],
)
def test_passthrough_path(path, expected):
    fs_mock = MagicMock()
    fs_mock.project_root = Path(os.getcwd())
    path = DagshubPath(fs_mock, path)
    actual = path.is_passthrough_path(fs_mock)
    assert actual == expected


def test_can_mount_multiple_in_different_dirs(mock_api):
    new_branch = "new"
    sha = secrets.token_hex(nbytes=20)
    mock_api.add_branch(new_branch, sha)

    _ = DagsHubFilesystem(project_root=".", repo_url="https://dagshub.com/user/repo")

    other_path = tempfile.mkdtemp()
    resp = mock_api._default_endpoints_and_responses()[1]["list_root"]
    mock_api.get(url=f"/api/v1/repos/user/repo/content/{sha}/").mock(resp)

    _ = DagsHubFilesystem(project_root=other_path, repo_url="https://dagshub.com/user/repo", branch=new_branch)


def test_path_isfile(mock_api, repo_with_hooks):
    path = "a.txt"  # a.txt is in the listdir of mock_api
    nonexistent_path = "nonexistent.txt"
    assert os.path.isfile(path)
    assert not os.path.isfile(nonexistent_path)


def test_path_isdir(mock_api, repo_with_hooks):
    path = "subdir"
    assert os.path.isdir(path)
    assert not os.path.isfile(path)

    nonexistent_dir = "subdir2"
    assert not os.path.isdir(nonexistent_dir)
    assert not os.path.isfile(nonexistent_dir)
