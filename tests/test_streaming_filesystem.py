import pytest
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
