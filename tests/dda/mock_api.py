import os.path

from httpx import Response
from respx import MockRouter, Route

BASE_REGEX = r"/api/v1/repos/\w+/\w+"


class MockApi(MockRouter):
    def __init__(self, git_repo, user="user", reponame="repo", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.reponame = reponame
        self.git_repo = git_repo

        self._endpoints, self._responses = self._default_endpoints_and_responses()
        route_dict = {
            k: (self._endpoints[k], self._responses[k]) for k in self._endpoints
        }
        for route_name in route_dict:
            endpoint_regex, return_value = route_dict[route_name]
            self.route(name=route_name, url__regex=endpoint_regex).mock(return_value)

    @property
    def repourlpath(self):
        return f"{self.user}/{self.reponame}"

    @property
    def repophysicalpath(self):
        return str(self.git_repo.workspace)

    @property
    def current_revision(self):
        heads = self.git_repo.api.heads
        if "main" in heads:
            return heads.main.commit.hexsha
        else:
            return heads.master.commit.hexsha

    @property
    def api_list_path(self):
        return f"/api/v1/repos/{self.repourlpath}/content/{self.current_revision}"

    @property
    def api_raw_path(self):
        return f"/api/v1/repos/{self.repourlpath}/raw/{self.current_revision}"

    def _default_endpoints_and_responses(self):
        endpoints = {
            "branch": rf"{BASE_REGEX}/branches/\w+",
            "branches": rf"{BASE_REGEX}/branches",
            "list_root": rf"{BASE_REGEX}/content/{self.current_revision}/$",
        }

        responses = {
            "branch": Response(
                200,
                json={
                    "name": "main",
                    "commit": {
                        "id": self.current_revision,
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
                            "id": self.current_revision,
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
            "list_root": Response(
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

        return endpoints, responses

    def add_file(self, path, content="aaa", status=200) -> Route:
        """
        Add a file to the api (only accessible via the raw endpoint)
        """
        route = self.route(url=f"{self.api_raw_path}/{path}")
        route.mock(Response(status, content=content))
        return route

    def add_dir(self, path, contents=[], status=200) -> Route:
        """
        Add a directory to the api (only accessible via the content endpoint)
        We don't keep a tree of added dirs, so it's not dynamic
        """
        route = self.route(url=f"{self.api_list_path}/{path}")
        content = [
            self.generate_list_entry(os.path.join(path, c[0]), c[1]) for c in contents
        ]
        route.mock(Response(status, json=content))
        return route

    def generate_list_entry(self, path, type="file"):
        return {
            "path": path,
            "type": type,
            "size": 0,
            "hash": "8586da76f372efa83d832a9d0e664817.dir",
            "versioning": "dvc",
            "download_url": f"https://dagshub.com/{self.repourlpath}/raw/{self.current_revision}/{path}",
        }
