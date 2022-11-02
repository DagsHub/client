import json

import requests
import urllib
import os
import logging
from typing import Union
from io import IOBase
from dagshub.common import config
from http import HTTPStatus
import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from requests.auth import HTTPBasicAuth

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"
DEFAULT_COMMIT_MESSAGE = "Upload files using DagsHub client"
REPO_CREATE_URL = "api/v1/user/repos"
ORG_REPO_CREATE_URL = "api/v1/org/{orgname}/repos"
USER_INFO_URL = "api/v1/user"
logger = logging.getLogger(__name__)


def get_default_branch(src_url, owner, reponame, auth):
    res = requests.get(urllib.parse.urljoin(src_url, REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')


def create_repo(repo_name, is_org=False, org_name="", description="", private=False, auto_init=False,
                gitignores="Python", license="", readme="", template="custom"):
    if template == "":
        template = "none"

    import dagshub.auth
    from dagshub.auth.token_auth import HTTPBearerAuth

    username = config.username
    password = config.password
    if username is not None and password is not None:
        auth = username, password
    else:
        token = config.token or dagshub.auth.get_token()
        if token is not None:
            auth = HTTPBearerAuth(token)

    if auth is None:
        raise RuntimeError("You can't create a repository without being authenticated.")

    if (license != "" or readme != "" or gitignores != "") and template == "none":
        template = "custom"

    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
        "gitignores": gitignores,
        "license": license,
        "readme": readme,
        "project_template": template,
    }

    url = REPO_CREATE_URL
    if is_org is True:
        url = ORG_REPO_CREATE_URL.format(
            orgname=org_name,
        )

    res = requests.post(
        urllib.parse.urljoin(config.host, url),
        data,
        auth=auth,
        headers=config.requests_headers
    )

    if res.status_code != HTTPStatus.CREATED:
        logger.error(f"Response ({res.status_code}):\n"
                     f"{res.content}")
        if res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            raise RuntimeError("Repository name is invalid or it already exists.")
        else:
            raise RuntimeError("Failed to create the desired repository.")

    repo = res.json()
    return Repo(owner=repo["owner"]["login"], name=repo["name"], token=token, branch="main")


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
            logger.debug("Branch wasn't provided. Fetching default branch...")
            self._set_default_branch()
        logger.debug(f"Set branch: {self.branch}")

    def upload(self, file: Union[str, IOBase], commit_message=DEFAULT_COMMIT_MESSAGE, path=None, **kwargs):
        file_for_upload = DataSet.get_file(file, path)
        self.upload_files([file_for_upload], commit_message=commit_message, **kwargs)

    def upload_files(self,
                     files,
                     directory_path="",
                     commit_message=DEFAULT_COMMIT_MESSAGE,
                     versioning=None,
                     new_branch=None,
                     last_commit=None,
                     force=False):

        data = {
            "commit_choice": "direct",
            "commit_summary": commit_message,
            "versioning": versioning,
            "last_commit": last_commit,
            "is_dvc_dir": directory_path != "" and versioning != "git",
        }

        if new_branch is not None:
            data.update({
                "commit_choice": "commit-to-new-branch",
                "new_branch_name": new_branch,
            })

        if force:
            data["last_commit"] = self._get_last_commit()
        logger.warning(f'Uploading {len(files)} files to "{self.full_name}"...')
        res = requests.put(
            self.get_request_url(directory_path),
            data,
            files=[("files", file) for file in files],
            auth=self.auth)
        self._log_upload_details(data, res, files)

    def _log_upload_details(self, data, res, files):
        logger.debug(f"Request URL: {res.request.url}\n"
                     f"Data:\n{json.dumps(data, indent=4)}\n"
                     f"Files:\n{json.dumps(list(map(str, files)), indent=4)}")
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
            logger.warning("Upload finished successfully!")

    @property
    def auth(self):
        if self.username is not None and self.password is not None:
            return HTTPBasicAuth(self.username, self.password)
        token = self.token or dagshub.auth.get_token(code_input_timeout=0)
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
    def __init__(self, repo: Repo, directory: str):
        self.files = {}
        self.repo = repo
        self.directory = self._clean_directory_name(directory)
        self.request_url = self.repo.get_request_url(directory)

    def add(self, file: Union[str, IOBase], path=None):
        path, file = self.get_file(file, path)
        if file is not None:
            if path in self.files:
                logger.warning(f"File already staged for upload on path \"{path}\". Overwriting")
            self.files[path] = (path, file)

    @staticmethod
    def _clean_directory_name(directory: str):
        return os.path.normpath(directory)

    @staticmethod
    def get_file(file: Union[str, IOBase], path=None):
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
                    return path, f
                except IsADirectoryError:
                    raise IsADirectoryError("'file' must describe a file, not a directory.")

            return path, file

        except Exception as e:
            logger.error(e)
            raise e

    def _reset_dataset(self):
        self.files.clear()

    def commit(self, commit_message=DEFAULT_COMMIT_MESSAGE, *args, **kwargs):
        file_list = list(self.files.values())
        self.repo.upload_files(file_list, self.directory, commit_message=commit_message, *args, **kwargs)
        self._reset_dataset()

    def _get_last_commit(self):
        api_path = f"api/v1/repos/{self.repo.full_name}/branches/{self.repo.branch}"
        api_url = urllib.parse.urljoin(self.repo.src_url, api_path)
        res = requests.get(api_url)
        if res.status_code == HTTPStatus.OK:
            content = res.json()
            try:
                return content["commit"]["id"]
            except KeyError:
                logger.error(f"Cannot get commit sha for branch '{self.repo.branch}'")
        return ""
