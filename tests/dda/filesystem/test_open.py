import logging

from dagshub.streaming import DagsHubFilesystem


def test_sets_current_revision(mock_api):
    fs = DagsHubFilesystem()
    assert fs._current_revision == mock_api.current_revision
    assert mock_api["branch"].called


def test_open(mock_api, repo_with_hooks):
    logging.basicConfig(level=logging.DEBUG)
    path = "a.txt"
    content = b"Hello, streaming world!"
    read_route = mock_api.add_file(path, content)
    with open(path, "rb") as f:
        assert f.read() == content
    assert read_route.called
