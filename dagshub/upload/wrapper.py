import json

import requests
import urllib
import os
import logging
from typing import Union
from io import IOBase
from dagshub.common import config
from http import HTTPStatus

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"
DEFAULT_COMMIT_MESSAGE = "Upload files using DagsHub client"
logger = logging.getLogger(__name__)


def get_default_branch(src_url, owner, reponame, auth):
    res = requests.get(urllib.parse.urljoin(src_url, REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame
    )))
    return res.json().get('default_branch')


class Repo:
    def __init__(self, owner, name, username=None, password=None, token=None, branch=None):
        self.owner = owner
        self.name = name
        self.src_url = config.host

        self.username = username or config.username
        self.password = password or config.password
        self.token = token or config.token
        self.branch = branch

        if self.branch is None:
            logger.info("Branch wasn't provided. Fetching default branch...")
            self._set_default_branch()
        logger.info(f"Set branch: {self.branch}")

    def upload(self,
               file: Union[str, IOBase],
               commit_message=None,
               versioning=None,
               new_branch=None,
               last_commit=None,
               path=None,
               force=False):

        ds = DataSet(self, ".")
        ds.add(file, path)
        ds.commit(commit_message, versioning, new_branch, last_commit, force)

    @property
    def auth(self):
        import dagshub.auth
        from dagshub.auth.token_auth import HTTPBearerAuth

        username = self.username or config.username
        password = self.password or config.password
        if username is not None and password is not None:
            return username, password
        try:
            token = self.token or dagshub.auth.get_token(code_input_timeout=0)
        except dagshub.auth.OauthNonInteractiveShellException:
            logger.debug("Failed to perform OAuth in a non interactive shell")
        if token is not None:
            return HTTPBearerAuth(token)

    def directory(self, path):
        return DataSet(self, path)

    def get_request_url(self, directory):
        return urllib.parse.urljoin(self.src_url, CONTENT_UPLOAD_URL.format(
            owner=self.owner,
            reponame=self.name,
            branch=self.branch,
            path=urllib.parse.quote(directory, safe="")
        ))

    def _set_default_branch(self):
        try:
            self.branch = get_default_branch(self.src_url, self.owner, self.name, self.auth)
        except Exception:
            raise RuntimeError(
                "Failed to get default branch for repository. "
                "Please specify a branch and make sure repository details are correct.")

    @property
    def full_name(self):
        return f"{self.owner}/{self.name}"


class DataSet:
    def __init__(self, repo: Repo, directory):
        self.files = []
        self.repo = repo
        self.directory = directory
        self.request_url = self.repo.get_request_url(directory)

    def add(self, file: Union[str, IOBase], path=None):
        try:
            # if path is not provided, fall back to the file name
            if path is None:
                try:
                    path = os.path.basename(os.path.normpath(file if type(file) is str else file.name))
                except Exception:
                    raise RuntimeError(
                        "Could not interpret your file's name. Please specify it in the keyword parameter 'path'.")

            if type(file) is str:
                try:
                    f = open(file, 'rb')
                    self.files.append((path, f))
                    return
                except IsADirectoryError:
                    raise IsADirectoryError("'file' must describe a file, not a directory.")

            self.files.append((path, file))

        except Exception as e:
            logger.error(e)
            raise e

    def _reset_dataset(self):
        self.files = []

    def commit(self, commit_message=None, versioning=None, new_branch=None, last_commit=None, force=False):
        data = {
            "commit_choice": "direct",
            "commit_message": commit_message,
            "versioning": versioning,
            "last_commit": last_commit,
            "is_dvc_dir": versioning != "git",
        }

        if new_branch is not None:
            data.update({
                "commit_choice": "commit-to-new-branch",
                "new_branch_name": new_branch,
            })

        if force:
            data["last_commit"] = self._get_last_commit()
        res = requests.put(
            self.request_url,
            data,
            files=[("files", file) for file in self.files],
            auth=self.repo.auth)
        self._log_upload_details(data, res)
        self._reset_dataset()

    def _get_last_commit(self):
        api_path = f"api/v1/repos/{self.repo.full_name}/branches/{self.repo.branch}"
        api_url = urllib.parse.urljoin(self.repo.src_url, api_path)
        res = requests.get(api_url)
        if res.status_code == HTTPStatus.OK:
            content = res.json()
            try:
                return content["commit"]["id"]
            except KeyError as e:
                logger.error(f"Cannot get commit sha for branch '{self.repo.branch}'")
        return ""

    def _log_upload_details(self, data, res):
        logger.debug(f"Request URL: {self.request_url}\n"
                     f"Data:\n{json.dumps(data, indent=4)}\n"
                     f"Files:\n{json.dumps(list(map(str, self.files)), indent=4)}")
        try:
            content = json.dumps(res.json(), indent=4)
        except Exception:
            content = res.content.decode("utf-8")

        if res.status_code != HTTPStatus.OK:
            logger.error(f"Response ({res.status_code}):\n"
                         f"{content}")
        else:
            logger.debug(f"Response ({res.status_code})\n")

        if res.status_code == 200:
            logger.info("Upload finished successfully!")
