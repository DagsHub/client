import os

import pytest

from dagshub.streaming import DagsHubFilesystem


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


def test_has_storage_bucket_paths(mock_api, repo_with_hooks):
    bucket_path = mock_api.storage_bucket_path
    bucket_path_elems = bucket_path.split("/")
    assert len(bucket_path_elems) == 2
    for root, dirs, files in os.walk("."):
        if root == ".":
            assert ".dagshub" in dirs
        elif root == "./.dagshub":
            assert "storage" in dirs
        elif root == "./.dagshub/storage":
            assert "s3" in dirs
        elif root == "./.dagshub/storage/s3":
            assert bucket_path_elems[0] in dirs
        elif root == f"./.dagshub/storage/s3/{bucket_path_elems[0]}":
            assert bucket_path_elems[1] in dirs


def test_lists_bucket_folder(mock_api, repo_with_hooks):
    files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    path = "testdir"
    mock_api.add_storage_dir(path, files)
    actual = os.listdir(f".dagshub/storage/s3/{mock_api.storage_bucket_path}/{path}")
    expected = [f[0] for f in files]
    assert set(actual) == set(expected)


def test_storage_pagination(mock_api, repo_with_hooks):
    files1 = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    files2 = [("c.txt", "file")]
    path = "testdir"
    # Order is important, otherwise respx loops and returns the first result indefinitely
    mock_api.add_storage_dir(path, files2, from_token="aaa")
    mock_api.add_storage_dir(path, files1, next_token="aaa")

    expected = [f[0] for f in files1 + files2]

    actual = os.listdir(f".dagshub/storage/s3/{mock_api.storage_bucket_path}/{path}")
    assert set(actual) == set(expected)


def test_binary(mock_api, repo_with_hooks):
    files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    path = "testdir"
    mock_api.add_dir(path, files)
    actual = os.listdir(path.encode("utf-8"))
    expected = [f[0].encode("utf-8") for f in files]
    assert set(actual) == set(expected)


def test_revision_pinning(mock_api, repourl, dagshub_repo):
    revision = "aaaabbbbcccc"
    mock_api.add_commit(revision)
    files = [("a.txt", "file"), ("b.txt", "file"), ("dir1", "dir")]
    path = "testdir"
    mock_api.add_dir("", [("testdir", "dir")], revision=revision)
    mock_api.add_dir(path, files, revision=revision)

    dfs = DagsHubFilesystem(project_root=".", repo_url=repourl, branch=revision)

    dfs.install_hooks()
    expected = [f[0] for f in files]
    actual = os.listdir("testdir")

    dfs.uninstall_hooks()

    assert set(actual) == set(expected)
