import logging

from dagshub.common.api.responses import RepoAPIResponse, BranchAPIResponse, CommitAPIResponse, StorageAPIEntry, \
    ContentAPIEntry, StorageContentAPIResult
from dagshub.common.util import multi_urljoin

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from typing import Optional, Tuple, Any, List

import dacite

import dagshub.auth
from dagshub.common import config

from dagshub.common.helpers import http_request

logger = logging.getLogger("dagshub")


class WrongRepoFormatError(Exception):
    pass


class RepoNotFoundError(Exception):
    pass


class BranchNotFoundError(Exception):
    pass


class CommitNotFoundError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class RepoAPI:

    def __init__(self, repo: str, host: Optional[str] = None, auth: Optional[Any] = None):
        """
        Class for interacting with the API of a repository

        :param repo (str): repo in the format of "user/repo"
        :param host (str): Optional: url of the dagshub instance to connect to
        :param auth: authentication to use to connect
        """
        self.owner, self.repo_name = self.parse_repo(repo)
        self.host = host if host is not None else config.host

        if auth is None:
            self.auth = dagshub.auth.get_authenticator(host=host)
        else:
            self.auth = auth

    def _http_request(self, method, url, **kwargs):
        if "auth" not in kwargs:
            kwargs["auth"] = self.auth
        return http_request(method, url, **kwargs)

    def get_repo_info(self) -> RepoAPIResponse:
        """
        Get information about the repository
        """
        res = self._http_request("GET", self.repo_api_url)

        if res.status_code == 404:
            raise RepoNotFoundError(f"Repo {self.repo_url} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting repository info."
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)
        return dacite.from_dict(RepoAPIResponse, res.json())

    def get_branch_info(self, branch: str) -> BranchAPIResponse:
        """
        Get information about specified branch
        """
        res = self._http_request("GET", self.branch_url(branch))

        if res.status_code == 404:
            raise BranchNotFoundError(f"Branch {branch} not found in repo {self.repo_url}")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting branch."
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)

        return dacite.from_dict(BranchAPIResponse, res.json())

    def get_commit_info(self, sha: str) -> CommitAPIResponse:
        """
        Get information about a specific commit
        """
        res = self._http_request("GET", self.commit_url(sha))

        if res.status_code == 404:
            raise BranchNotFoundError(f"Commit {sha} not found in repo {self.repo_url}")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting commit."
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)

        return dacite.from_dict(CommitAPIResponse, res.json()["commit"])

    def get_connected_storages(self) -> List[StorageAPIEntry]:
        """
        Get storages that are connected to the repository
        """
        res = self._http_request("GET", self.storage_api_url())

        if res.status_code == 404:
            raise RepoNotFoundError(f"Repo {self.repo_url} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting repository info."
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)

        return [dacite.from_dict(StorageAPIEntry, storage_entry) for storage_entry in res.json()]

    def list_path(self, path: str, revision: Optional[str] = None, include_size: bool = False) -> List[ContentAPIEntry]:
        """
        Get listing of everything in the specified path
        """
        params = {
            "include_size": include_size
        }
        res = self._http_request("GET", self.content_api_url(path, revision), params=params)

        if res.status_code == 404:
            raise PathNotFoundError(f"Path {path} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when listing path {path}"
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)

        content = res.json()
        if type(content) == dict:
            content = [content]
        return [dacite.from_dict(ContentAPIEntry, entry) for entry in content]

    def list_storage_path(self, path: str, include_size: bool = False) -> List[ContentAPIEntry]:
        """
        Get listing of everything in the specified storage path
        Path format: <scheme>/<bucket-name>/<path>
        Example: s3/my-bucket/prefix/path/to/file
        """
        params = {
            "include_size": include_size,
            "paging": True
        }

        url = self.storage_content_api_url(path)
        has_next_page = True

        def _get():
            res = self._http_request("GET", url, params=params)

            if res.status_code == 404:
                raise PathNotFoundError(f"Path {path} not found")
            elif res.status_code >= 400:
                error_msg = f"Got status code {res.status_code} when listing path {path}"
                logger.error(error_msg)
                logger.debug(res.content)
                raise RuntimeError(error_msg)

            return dacite.from_dict(StorageContentAPIResult, res.json())

        entries = []

        while has_next_page:
            has_next_page = False
            resp = _get()
            entries += resp.entries
            if resp.next_token is not None:
                has_next_page = True
                params["from_token"] = resp.next_token

        return entries

    def get_file(self, path: str, revision: Optional[str] = None) -> bytes:
        """
        Download file from repo
        """
        res = self._http_request("GET", self.raw_api_url(path, revision))
        if res.status_code == 404:
            raise PathNotFoundError(f"Path {path} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting file {path}"
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)
        return res.content

    def get_storage_file(self, path: str) -> bytes:
        """
        Download file from storage
        Path format: <scheme>/<bucket-name>/<path>
        Example: s3/my-bucket/prefix/path/to/file
        """
        res = self._http_request("GET", self.storage_raw_api_url(path))
        if res.status_code == 404:
            raise PathNotFoundError(f"Path {path} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting file {path}"
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)
        return res.content

    @cached_property
    def default_branch(self) -> str:
        return self.get_repo_info().default_branch

    @cached_property
    def id(self) -> int:
        return self.get_repo_info().id

    @cached_property
    def is_mirror(self) -> bool:
        return self.get_repo_info().mirror

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo_name}"

    def last_commit(self, branch: Optional[str] = None) -> CommitAPIResponse:
        if branch is None:
            branch = self.default_branch
        return self.get_branch_info(branch).commit

    def last_commit_sha(self, branch: Optional[str] = None) -> str:
        return self.last_commit(branch).id

    @cached_property
    def repo_api_url(self) -> str:
        """
        Base URL for making all API request for the repos.
        Format: https://dagshub.com/api/v1/repos/user/repo
        """
        return multi_urljoin(
            self.host,
            "api/v1/repos",
            self.owner,
            self.repo_name,
        )

    @cached_property
    def repo_url(self) -> str:
        """
        URL of the repo on DagsHub
        Format: https://dagshub.com/user/repo
        """
        return multi_urljoin(
            self.host,
            self.owner,
            self.repo_name
        )

    def branch_url(self, branch) -> str:
        """
        URL of a branch on the repo
        Format: https://dasghub.com/api/v1/repos/user/repo/branches/branch
        """
        return multi_urljoin(
            self.repo_api_url,
            "branches",
            branch
        )

    @cached_property
    def data_engine_url(self) -> str:
        """
        URL of data engine
        """
        return multi_urljoin(
            self.repo_api_url,
            "data-engine"
        )

    @cached_property
    def annotations_url(self) -> str:
        return multi_urljoin(
            self.repo_api_url,
            "annotations"
        )

    def commit_url(self, sha) -> str:
        """
        URL of a commit in the repo
        Format: https://dagshub.com/api/v1/repos/user/repo/commits/sha
        """
        return multi_urljoin(
            self.repo_api_url,
            "commits",
            sha
        )

    def content_api_url(self, path: str, revision: Optional[str] = None) -> str:
        """
        URL for Content API access
        Format: https://dagshub.com/api/v1/repos/user/repo/content/revision/path
        """
        if revision is None:
            revision = self.default_branch
        return multi_urljoin(
            self.repo_api_url,
            "content",
            revision,
            path
        )

    def raw_api_url(self, path: str, revision: Optional[str] = None) -> str:
        """
        URL for Raw Content API access
        Format: https://dagshub.com/api/v1/repos/user/repo/raw/revision/path
        """
        if revision is None:
            revision = self.default_branch
        return multi_urljoin(
            self.repo_api_url,
            "raw",
            revision,
            path
        )

    def storage_content_api_url(self, path: str) -> str:
        """
        URL for Storage Content API access
        path example: s3/bucket-name/path/in/bucket
        Format: https://dagshub.com/api/v1/repos/user/repo/storage/content/path
        """
        return multi_urljoin(
            self.repo_api_url,
            "storage/content",
            path
        )

    def storage_raw_api_url(self, path: str) -> str:
        """
        URL for Storage Raw Content API access
        path example: s3/bucket-name/path/in/bucket
        Format: https://dagshub.com/api/v1/repos/user/repo/storage/raw/path
        """
        return multi_urljoin(
            self.repo_api_url,
            "storage/raw",
            path
        )

    def storage_api_url(self) -> str:
        """
        URL for getting connected storages
        Format: https://dagshub.com/api/v1/repos/user/repo/storage
        """
        return multi_urljoin(self.repo_api_url, "storage")

    @staticmethod
    def parse_repo(repo: str) -> Tuple[str, str]:
        repo = repo.strip("/")
        parts = repo.split("/")
        if len(parts) != 2:
            raise WrongRepoFormatError("repo needs to be in the format <repo-owner>/<repo-name>")
        return parts[0], parts[1]
