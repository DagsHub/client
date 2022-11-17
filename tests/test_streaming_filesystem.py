import logging

import pytest
from httpx import Response

from dagshub.streaming import DagsHubFilesystem
from pathlib import Path
import os


@pytest.fixture(autouse=True)
def mock_env_vars():
    # Skip auth
    os.environ["DAGSHUB_USER_TOKEN"] = "token"


def test_sets_current_revision(mock_api, dagshub_repo, current_revision):
    fs = DagsHubFilesystem()
    assert fs._current_revision == current_revision
    assert mock_api["branch"].called


def test_open(mock_api, repo_with_hooks, api_raw_path):
    logging.basicConfig(level=logging.DEBUG)
    path = "dvc_file.txt"
    content = b"Hello world"
    raw_route = mock_api.route(url=f"{api_raw_path}/{path}")
    raw_route.mock(Response(200, content=content))
    with open(path, "rb") as f:
        assert f.read() == content
    assert raw_route.called


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
    path = Path(path)
    actual = DagsHubFilesystem._passthrough_path(path)
    assert actual == expected
