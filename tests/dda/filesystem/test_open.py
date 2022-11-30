import os.path
import pytest
from dagshub.streaming import DagsHubFilesystem


def test_sets_current_revision(mock_api):
    fs = DagsHubFilesystem()
    assert fs._current_revision == mock_api.current_revision
    assert mock_api["branch"].called


def test_open(mock_api, repo_with_hooks):
    path = "a.txt"
    content = b"Hello, streaming world!"
    read_route = mock_api.add_file(path, content)
    with open(path, "rb") as f:
        assert f.read() == content
    assert read_route.called


def test_open_nested_path(mock_api, repo_with_hooks):
    path = "nested/path/a.txt"
    content = b"Hello, streaming world!"
    mock_api.add_file(path, content)
    with open(path, "rb") as f:
        assert f.read() == content
    print(os.path.dirname(path))
    assert os.path.exists(os.path.dirname(path))


def test_open_for_write(mock_api, repo_with_hooks):
    content = "adfasdf"
    path = "new_file.txt"
    with open(path, "w") as f:
        f.write(content)
    with open(path, "r") as f:
        assert f.read() == content


def test_nested_open_for_write(mock_api, repo_with_hooks):
    content = "adfasdf"
    path = "aaaa/bbb/new_file.txt"
    mock_api.add_dir("aaaa", contents=[("bbb", "dir")])
    mock_api.add_dir("aaaa/bbb")
    with open(path, "w") as f:
        f.write(content)
    with open(path, "r") as f:
        assert f.read() == content


def test_nested_open_throws_nonexistent_dir(mock_api, repo_with_hooks):
    content = "adfasdf"
    path = "nonexistent/dir/new_file.txt"
    mock_api.add_dir("nonexistent", status=404)
    with pytest.raises(FileNotFoundError):
        with open(path, "w") as f:
            f.write(content)
