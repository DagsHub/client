import os
import pytest

import dagshub.streaming


def scandir_to_dict(scandir_iter):
    res = {}
    for f in scandir_iter:
        res[f.name] = f.path
    return res


@pytest.fixture
def scandir_mock(mock_api):
    mock_api.add_dir("temp", [("b.txt", "file")])
    yield mock_api


@pytest.mark.parametrize(
    "cwd, path",
    [
        (".", "temp"),
    ],
)
def test_scandir(scandir_mock, cwd, path):
    """
    Tests that DagsHubFilesystem behaves the same way as os.scandir()
    """
    # Assuming we only need to create one directory
    relpath = os.path.basename(path)
    os.mkdir(relpath)
    open(os.path.join(relpath, "a.txt"), "w").close()
    fs = dagshub.streaming.DagsHubFilesystem()
    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.chdir(cwd)
            expected = scandir_to_dict(os.scandir(path))
            fs.install_hooks()
            actual = scandir_to_dict(os.scandir(path))
            assert "b.txt" in actual
            del actual["b.txt"]
            assert expected == actual
    finally:
        fs.uninstall_hooks()


def test_abspath(scandir_mock):
    # Need to do it separately instead of in parametrize because one of the fixtures changes the cwd
    test_scandir(scandir_mock, ".", os.path.abspath("temp"))


def test_nested(scandir_mock):
    repodir = os.path.basename(os.getcwd())
    test_scandir(scandir_mock, "..", f"{repodir}/temp")


def test_up(scandir_mock):
    repodir = os.path.basename(os.getcwd())
    test_scandir(scandir_mock, ".", f"../{repodir}/temp")
