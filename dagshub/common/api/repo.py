import logging
from functools import cached_property
from typing import Optional, Tuple

import dacite

import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
import httpx
from urllib.parse import urljoin, quote_plus

from dagshub.common.api.responses import RepoAPIResponse, BranchAPIResponse

logger = logging.getLogger("dagshub")


class WrongRepoFormatError(Exception):
    pass


class RepoNotFoundError(Exception):
    pass


class BranchNotFoundError(Exception):
    pass


class RepoAPI:

    def __init__(self, repo: str, host: Optional[str] = None):
        self.owner, self.repo_name = self.parse_repo(repo)
        self.host = host if host is not None else config.host

        self.client = httpx.Client(
            auth=HTTPBearerAuth(config.token or dagshub.auth.get_token(host=self.host))
        )
        print("Done")

    def get_repo_info(self) -> RepoAPIResponse:
        res = self.client.get(self.repo_api_url)

        if res.status_code == 404:
            raise RepoNotFoundError(f"Repo {self.repo_url} doesn't exist")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting repository info."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return dacite.from_dict(RepoAPIResponse, res.json())

    def get_branch_info(self, branch: str):
        res = self.client.get(self.branch_url(branch))

        if res.status_code == 404:
            raise BranchNotFoundError(f"Branch {branch} not found in repo {self.repo_url}")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when getting branch."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return dacite.from_dict(BranchAPIResponse, res.json())

    @cached_property
    def default_branch(self) -> str:
        return self.get_repo_info().default_branch

    @property
    def last_commit(self, branch: Optional[str] = None) -> str:
        if branch is None:
            branch = self.default_branch
        return self.get_branch_info(branch).commit.id

    @cached_property
    def repo_api_url(self) -> str:
        """
        Base URL for making all API request for the repos.
        Format: https://dagshub.com/api/v1/repos/user/repo
        """
        return _multi_urljoin(
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
        return _multi_urljoin(
            self.host,
            self.owner,
            self.repo_name
        )

    def branch_url(self, branch) -> str:
        """
        URL of a branch on the repo
        Format: https://dasghub.com/api/v1/repos/user/repo/branches/branch
        """
        return _multi_urljoin(
            self.repo_api_url,
            "branches",
            branch
        )

    @staticmethod
    def parse_repo(repo: str) -> Tuple[str, str]:
        parts = repo.split("/")
        if len(parts) != 2:
            raise WrongRepoFormatError("repo needs to be in the format <repo-owner>/<repo-name>")
        return tuple(parts)


def _multi_urljoin(*parts):
    """Shoutout to https://stackoverflow.com/a/55722792"""
    return urljoin(parts[0] + "/", "/".join(quote_plus(part.strip("/"), safe="/") for part in parts[1:]))
