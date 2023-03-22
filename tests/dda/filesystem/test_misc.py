import os.path
from unittest.mock import MagicMock

import pytest
from pathlib import Path
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
    path = DagshubPath(fs_mock, Path(os.path.abspath(path)), Path(path))
    actual = path.is_passthrough_path
    assert actual == expected
