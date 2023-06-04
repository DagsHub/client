import os.path

from httpx import Response
from respx import MockRouter, Route


class MockApi(MockRouter):
    def __init__(self, git_repo, user="user", reponame="repo", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.reponame = reponame
        self.git_repo = git_repo

        self.storage_bucket_path = "storage-bucket/prefix"

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
    def repoapipath(self):
        return f"/api/v1/repos/{self.repourlpath}"

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

    def api_list_path(self, branch=None):
        if branch is None:
            branch = self.current_revision
        return f"{self.repoapipath}/content/{branch}"

    def api_raw_path(self, branch=None):
        if branch is None:
            branch = self.current_revision
        return f"{self.repoapipath}/raw/{branch}"

    @property
    def api_storage_list_path(self):
        return f"{self.repoapipath}/storage/content/s3/{self.storage_bucket_path}"

    @property
    def api_storage_raw_path(self):
        return f"{self.repoapipath}/storage/raw/s3/{self.storage_bucket_path}"

    def _default_endpoints_and_responses(self):
        endpoints = {
            "repo": rf"{self.repoapipath}/?$",
            "branch": rf"{self.repoapipath}/branches/(main|master)$",
            "branches": rf"{self.repoapipath}/branches/?$",
            "list_root": rf"{self.repoapipath}/content/{self.current_revision}/$",
            "storages": rf"{self.repoapipath}/storage/?$"
        }

        responses = {
            "repo": Response(
                200,
                json={
                    "id": 713,
                    "owner": {
                        "id": 736,
                        "login": self.user,
                        "full_name": self.user,
                        "avatar_url": "https://dagshub.com/avatars/736",
                        "username": self.user,
                    },
                    "name": self.reponame,
                    "full_name": self.repourlpath,
                    "description": "Open Source Data Science (OSDS) Monocular Depth Estimation "
                                   "– Turn 2d photos into 3d photos – show your grandma the awesome results.",
                    "private": False,
                    "fork": False,
                    "parent": None,
                    "empty": False,
                    "mirror": False,
                    "size": 19987456,
                    "html_url": f"https://dagshub.com/{self.repourlpath}",
                    "clone_url": f"https://dagshub.com/{self.repourlpath}.git",
                    "website": "",
                    "stars_count": 12,
                    "forks_count": 25,
                    "watchers_count": 5,
                    "open_issues_count": 6,
                    "default_branch": "main",
                    "created_at": "2020-08-02T15:19:07Z",
                    "updated_at": "2023-02-01T16:06:44Z",
                    "permissions": {"admin": False, "push": False, "pull": False},
                },
            ),
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
                        "content_url": "some_url",
                    },
                    {
                        "path": "b.txt",
                        "type": "file",
                        "size": 0,
                        "hash": "some_hash",
                        "versioning": "dvc",
                        "download_url": "some_url",
                        "content_url": "some_url",
                    },
                    {
                        "path": "c.txt",
                        "type": "file",
                        "size": 0,
                        "hash": "some_hash",
                        "versioning": "dvc",
                        "download_url": "some_url",
                        "content_url": "some_url",
                    },
                    {
                        "path": "a.txt.dvc",
                        "type": "file",
                        "size": 0,
                        "hash": "some_hash",
                        "versioning": "git",
                        "download_url": "some_url",
                        "content_url": "some_url",
                    },
                ],
            ),
            "storages": Response(
                200,
                json=[
                    {
                        "name": self.storage_bucket_path,
                        "protocol": "s3",
                        "list_path": f"{self.repoapipath}/storage/content/s3/{self.storage_bucket_path}"
                    }
                ]
            )
        }

        return endpoints, responses

    def add_file(self, path, content="aaa", status=200, is_storage=False, revision=None) -> Route:
        """
        Add a file to the api (only accessible via the raw endpoint)
        """

        # TODO: add branch
        if is_storage:
            route = self.route(url=f"{self.api_storage_raw_path}/{path}")
        else:
            route = self.route(url=f"{self.api_raw_path(revision)}/{path}")
        route.mock(Response(status, content=content))
        return route

    def add_dir(self, path, contents=[], status=200, is_storage=False, revision=None) -> Route:
        """
        Add a directory to the api (only accessible via the content endpoint)
        We don't keep a tree of added dirs, so it's not dynamic
        """

        # TODO: add branch
        if is_storage:
            route = self.route(url=f"{self.api_storage_list_path}/{path}")
        else:
            route = self.route(url=f"{self.api_list_path(revision)}/{path}")
        content = [
            self.generate_list_entry(os.path.join(path, c[0]), c[1]) for c in contents
        ]
        route.mock(Response(status, json=content))
        return route

    def add_storage_dir(self, path, contents=[], from_token=None, next_token=None, status=200):
        """
        Add a directory to the storage api
        Storage has a different response schema
        """
        url = f"{self.api_storage_list_path}/{path}?paging=true"
        if from_token is not None:
            url += f"&from_token={from_token}"
        route = self.route(url=url)
        content = {
            "entries": [
                self.generate_list_entry(os.path.join(path, c[0]), c[1]) for c in contents
            ],
            "limit": len(contents),
        }
        if next_token is not None:
            content["next_token"] = next_token
        route.mock(Response(status, json=content))
        return route

    def enable_uploads(self, branch="main"):
        route = self.put(
            name="upload", url__regex=f"api/v1/repos/{self.repourlpath}/content/{branch}/.*"
        )
        route.mock(Response(200))
        return route

    def generate_list_entry(self, path, entry_type="file"):
        return {
            "path": path,
            "type": entry_type,
            "size": 0,
            "hash": "8586da76f372efa83d832a9d0e664817.dir",
            "versioning": "dvc",
            "download_url": f"https://dagshub.com/{self.repourlpath}/raw/{self.current_revision}/{path}",
            "content_url": f"https://dagshub.com/{self.repourlpath}/content/{self.current_revision}/{path}",
        }

    def add_branch(self, branch, revision):
        resp_json = {
            "name": branch,
            "commit": {
                "id": revision,
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
            }
        }
        branch_route = self.get(url=f"/api/v1/repos/{self.repourlpath}/branches/{branch}")
        branch_route.mock(Response(200, json=resp_json))
        return branch_route

    def add_commit(self, revision):
        resp_json = {
            "commit": {
                "id": revision,
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
            }
        }
        branch_route = self.get(url=f"/api/v1/repos/{self.repourlpath}/commits/{revision}")
        branch_route.mock(Response(200, json=resp_json))
        return branch_route
