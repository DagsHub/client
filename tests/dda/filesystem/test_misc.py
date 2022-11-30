import pytest
from pathlib import Path
from dagshub.streaming import DagsHubFilesystem


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
