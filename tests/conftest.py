import os

import pytest
import respx

from httpx import Response

import dagshub.streaming


@pytest.fixture
def repouser():
    return "user"


@pytest.fixture
def reponame():
    return "repo"


@pytest.fixture
def current_revision(dagshub_repo):
    return dagshub_repo.api.heads.main.commit.hexsha


@pytest.fixture
def repopath(repouser, reponame):
    return f"{repouser}/{reponame}"


@pytest.fixture
def api_lookup(current_revision):
    responses = {
        "branch": Response(
            200,
            json={
                "name": "main",
                "commit": {
                    "id": current_revision,
                    "message": "Update 'README.md'\n",
                    "url": "",
                    "author": {
                        "name": "dagshub",
                        "email": "info@dagshub.com",
                        "username": "",
                    },
                    "committer": {
                        "name": "dagshub",
                        "email": "info@dagshub.com",
                        "username": "",
                    },
                    "added": None,
                    "removed": None,
                    "modified": None,
                    "timestamp": "2021-08-10T09:03:32Z",
                },
            },
        ),
        "branches": Response(
            200,
            json=[
                {
                    "name": "main",
                    "commit": {
                        "id": current_revision,
                        "message": "Update 'README.md'\n",
                        "url": "",
                        "author": {
                            "name": "dagshub",
                            "email": "info@dagshub.com",
                            "username": "",
                        },
                        "committer": {
                            "name": "dagshub",
                            "email": "info@dagshub.com",
                            "username": "",
                        },
                        "added": None,
                        "removed": None,
                        "modified": None,
                        "timestamp": "2021-08-10T09:03:32Z",
                    },
                }
            ],
        ),
        "list": Response(
            200,
            json=[
                {
                    "path": "a.txt",
                    "type": "file",
                    "size": 0,
                    "hash": "some_hash",
                    "versioning": "dvc",
                    "download_url": "some_url",
                },
                {
                    "path": "b.txt",
                    "type": "file",
                    "size": 0,
                    "hash": "some_hash",
                    "versioning": "dvc",
                    "download_url": "some_url",
                },
                {
                    "path": "c.txt",
                    "type": "file",
                    "size": 0,
                    "hash": "some_hash",
                    "versioning": "dvc",
                    "download_url": "some_url",
                },
                {
                    "path": "a.txt.dvc",
                    "type": "file",
                    "size": 0,
                    "hash": "some_hash",
                    "versioning": "git",
                    "download_url": "some_url",
                },
            ],
        ),
    }

    base_regex = r"/api/v1/repos/\w+/\w+"

    endpoints = {
        "branch": rf"{base_regex}/branches/\w+",
        "branches": rf"{base_regex}/branches",
        "list": rf"{base_regex}/content/\w+/.*",
    }

    return {endpoints[k]: responses.get(k) for k in endpoints}


@pytest.fixture
def mock_api(api_lookup):
    with respx.mock(
        base_url="https://dagshub.com", assert_all_called=False
    ) as respx_mock:
        for endpoint_regex, return_value in api_lookup.items():
            respx_mock.get(url__regex=endpoint_regex).mock(return_value)
        yield respx_mock


@pytest.fixture
def dagshub_repo(git_repo, repopath):
    cwd = os.getcwd()
    os.chdir(git_repo.workspace)
    repo = git_repo.api
    # Add remote
    repo.create_remote("origin", f"https://dagshub.com/{repopath}.git")
    # Create an initial commit
    filename = "test_git_file.txt"
    open(filename, "wb").close()
    repo.index.add([filename])
    repo.index.commit("initial commit")
    yield git_repo
    os.chdir(cwd)


@pytest.fixture
def install_hooks(dagshub_repo):
    dagshub.streaming.install_hooks()
    yield
    dagshub.streaming.uninstall_hooks()
