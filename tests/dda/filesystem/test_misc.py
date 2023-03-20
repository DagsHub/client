import os.path
import secrets
import tempfile
from unittest.mock import MagicMock

import pytest
from pathlib import Path

from dagshub.streaming import DagsHubFilesystem
from dagshub.streaming.dataclasses import DagshubPath, DagshubPathType
from dagshub.streaming.errors import FilesystemAlreadyMountedError


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
    path = DagshubPath(fs_mock, Path(os.path.abspath(path)), Path(path))
    actual = DagshubPathType.PASSTHROUGH_PATH in path.path_type
    assert actual == expected


def test_cant_mount_multiples_in_same_dir(mock_api):
    new_branch = "new"
    sha = secrets.token_hex(nbytes=20)
    mock_api.add_branch(new_branch, sha)
    fs = DagsHubFilesystem(project_root=".", repo_url="https://dagshub.com/user/repo")
    with pytest.raises(FilesystemAlreadyMountedError):
        fs_new = DagsHubFilesystem(project_root=".", repo_url="https://dagshub.com/user/repo", branch=new_branch)

def test_can_mount_multiple_in_different_dirs(mock_api):
    new_branch = "new"
    sha = secrets.token_hex(nbytes=20)
    mock_api.add_branch(new_branch, sha)

    fs = DagsHubFilesystem(project_root=".", repo_url="https://dagshub.com/user/repo")

    other_path = tempfile.mkdtemp()
    resp = mock_api._default_endpoints_and_responses()[1]["list_root"]
    mock_api.get(url=f"/api/v1/repos/user/repo/content/{sha}/").mock(resp)

    fs_new = DagsHubFilesystem(project_root=other_path, repo_url="https://dagshub.com/user/repo", branch=new_branch)

