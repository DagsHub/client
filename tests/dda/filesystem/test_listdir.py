import os

import pytest


def test_listdir(mock_api, repo_with_hooks):
    files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    path = "testdir"
    mock_api.add_dir(path, files)
    actual = os.listdir(path)
    expected = [f[0] for f in files]
    # Compare sets to ignore order of the lists
    assert set(actual) == set(expected)


def test_listdir_includes_local_files(mock_api, repo_with_hooks):
    path = "testdir"
    os.mkdir(path)
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(path)
        files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
        mock_api.add_dir(path, files)
        add_file = "c.txt"
        with open(add_file, "w") as f:
            f.write("test")

        expected = [f[0] for f in files]
        expected.append(add_file)

        actual = os.listdir(".")
        assert set(expected) == set(actual)


def test_binary(mock_api, repo_with_hooks):
    files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    path = "testdir"
    mock_api.add_dir(path, files)
    actual = os.listdir(path.encode("utf-8"))
    expected = [f[0].encode("utf-8") for f in files]
    assert set(actual) == set(expected)
