import os.path
from pathlib import PosixPath
from typing import List, Dict, Optional

from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common.api import RepoAPI
from dagshub.common.api.repo import PathNotFoundError
from dagshub.common.api.responses import StorageAPIEntry, RepoAPIResponse, ContentAPIEntry

from typing_extensions import Self


class MockError(Exception):
    ...


class MockRepoAPI(RepoAPI):
    def __init__(self, repo: str):
        super().__init__(repo, "http://some-nonesitent-domain.localhost", HTTPBearerAuth("faketoken"))
        self.storages: List[StorageAPIEntry] = []
        self._default_branch = "main"
        self.repo_files: Dict[str, Dict[str, bytes]] = {}
        self.storage_files: Dict[str, bytes] = {}

        self.repo_contents: Dict[str, Dict[str, List[ContentAPIEntry]]] = {}
        self.storage_contents: Dict[str, List[ContentAPIEntry]] = {}

        # Add dagshub storage
        self.add_storage("s3", self.repo_name)

    def _http_request(self, method, url, **kwargs):
        raise MockError(f"_http_request {method} called at url {url}. See the stack trace to find unmocked function")

    def add_storage(self, protocol: str, name: str):
        self.storages.append(StorageAPIEntry(name, protocol, "random-url"))
        contentEntry = ContentAPIEntry(
            path=f"{protocol}/{name}",
            type="storage",
            size=0,
            hash="randomhash",
            versioning="bucket",
            download_url="randomurl",
            content_url="randomcontenturl",
        )
        self.add_repo_contents("", entries=[contentEntry])

    def add_repo_file(self, path: str, content: bytes, revision=None):
        if revision is None:
            revision = self.default_branch
        if revision not in self.repo_files:
            self.repo_files[revision] = {}
        self.repo_files[revision][path] = content
        # TODO: this doesn't actually resolve directories that get generated as a result
        self.add_repo_contents(os.path.dirname(path), revision, files=[path])

    def add_dagshub_storage_file(self, path: str, content: bytes):
        self.add_storage_file(f"s3/{self.repo_name}/{path}", content)

    def add_storage_file(self, path: str, content: bytes):
        self.storage_files[path] = content
        self.add_storage_contents(os.path.dirname(path), files=[path])

    def add_repo_contents(
        self,
        path: str,
        revision: Optional[str] = None,
        files: Optional[List[str]] = None,
        dirs: Optional[List[str]] = None,
        entries: Optional[List[ContentAPIEntry]] = None,
    ):
        files = files if files is not None else []
        dirs = dirs if dirs is not None else []
        entries = entries if entries is not None else []
        if revision is None:
            revision = self.default_branch
        if revision not in self.repo_contents:
            self.repo_contents[revision] = {}
        if path not in self.repo_contents[revision]:
            self.repo_contents[revision][path] = []
        entries.extend([self.generate_content_api_entry(x) for x in files])
        entries.extend([self.generate_content_api_entry(x, True) for x in dirs])
        self.repo_contents[revision][path].extend(entries)

    def add_storage_contents(
        self,
        path: str,
        files: Optional[List[str]] = None,
        dirs: Optional[List[str]] = None,
        entries: Optional[List[ContentAPIEntry]] = None,
    ):
        files = files if files is not None else []
        dirs = dirs if dirs is not None else []
        entries = entries if entries is not None else []
        if path not in self.storage_contents:
            self.storage_contents[path] = []
        entries.extend([self.generate_content_api_entry(x, versioning="bucket") for x in files])
        entries.extend([self.generate_content_api_entry(x, True, versioning="bucket") for x in dirs])
        self.storage_contents[path].extend(entries)

    def add_dagshub_storage_contents(self, path, **kwargs):
        self.add_storage_contents(path=f"s3/{self.repo_name}/{path}", **kwargs)


    @staticmethod
    def generate_content_api_entry(path, is_dir=False, versioning="dvc") -> ContentAPIEntry:
        return ContentAPIEntry(
            path=path,
            type="dir" if is_dir else "file",
            size=0,
            hash="randomhash",
            versioning=versioning,
            download_url="randomurl",
            content_url="randomcontenturl",
        )

    @property
    def default_branch(self) -> str:
        return self._default_branch

    def get_connected_storages(self) -> List[StorageAPIEntry]:
        return self.storages

    def get_file(self, path: str, revision: Optional[str] = None) -> bytes:
        if revision is None:
            revision = self.default_branch
        content = self.repo_files.get(revision, {}).get(path)
        if content is None:
            raise PathNotFoundError
        return content

    def get_storage_file(self, path: str) -> bytes:
        content = self.storage_files.get(path)
        if content is None:
            raise PathNotFoundError
        return content

    def list_path(self, path: str, revision: Optional[str] = None, include_size: bool = False) -> List[ContentAPIEntry]:
        if revision is None:
            revision = self.default_branch
        content = self.repo_contents.get(revision, {}).get(path)
        if content is None:
            raise PathNotFoundError
        return content

    def list_storage_path(self, path: str, include_size: bool = False) -> List[ContentAPIEntry]:
        content = self.storage_contents.get(path)
        if content is None:
            raise PathNotFoundError
        return content
