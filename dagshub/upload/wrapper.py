import json
import posixpath

import urllib
import os
import logging
import fnmatch
from typing import Union
from io import IOBase
import httpx
import rich.progress

from dagshub.common import config, helpers, rich_console
from http import HTTPStatus
import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.upload.errors import determine_upload_api_error
from dagshub.common.helpers import log_message

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
DEFAULT_COMMIT_MESSAGE = "Upload files using DagsHub client"
DEFAULT_DATASET_COMMIT_MESSAGE = "Initial dataset commit"
REPO_CREATE_URL = "api/v1/user/repos"
ORG_REPO_CREATE_URL = "api/v1/org/{orgname}/repos"
USER_INFO_URL = "api/v1/user"
DEFAULT_DATA_DIR_NAME = 'data'
logger = logging.getLogger(__name__)

s = httpx.Client()
s.timeout = config.http_timeout
s.follow_redirects = True
s.headers.update(config.requests_headers)


def create_dataset(repo_name, local_path, glob_exclude="", org_name="", private=False):
    """
    Create a new repository on DagsHub and upload an entire dataset to it
    :param repo_name (str): Name of the repository to be created
    :param local_path (str): local path where the dataset to upload is located
    :param glob_exclude (str): regex to exclude certain files from the upload process
    :param org_name (str): Organization name to be the repository owner
    :param private (bool): Flag to indicate the repository is going to be private
    :return : Repo object of the repository created
    """
    repo = create_repo(repo_name, org_name=org_name, private=private)
    dir = repo.directory(repo_name)
    dir.add_dir(local_path, glob_exclude, commit_message=DEFAULT_DATASET_COMMIT_MESSAGE)
    return repo


def add_dataset_to_repo(repo,
                        local_path,
                        data_dir=DEFAULT_DATA_DIR_NAME):
    """
    Given a repository created on dagshub - upload an entire dataset to it
    :param reo (Reop): repository created beforehand
    :param local_path (str): local path where the dataset to upload is located
    :param data_dir (str): name of data directory that will be created inside repo
    """
    dir = repo.directory(data_dir)
    dir.add_dir(local_path, commit_message=DEFAULT_DATASET_COMMIT_MESSAGE)


def create_repo(
    repo_name,
    org_name="",
    description="",
    private=False,
    auto_init=False,
    gitignores="Python",
    license="",
    readme="",
    template="custom",
    host=""
):
    """
    Creates a repository on DagsHub for the current user (default) or an organization passed as an argument

    :param repo_name (str): Name of the repository to be created
    :param org_name (str): Organization name to be the repository owner
    :param description (str): Description for the repository
    :param private (bool): Flag to indicate the repository is going to be private
    :param gitignores (str): Which gitignore template(s) to use (comma separated string)
    :param license (str): Which license file to use
    :param readme (str): Readme file path to upload
    :param template (str): Which project template to use, options are: none, custom, notebook-template,
    cookiecutter-dagshub-dvc. To learn more, check out https://dagshub.com/docs/feature_guide/project_templates/
    :return: Repo object of the repository created
    """
    if template == "":
        template = "none"

    import dagshub.auth
    from dagshub.auth.token_auth import HTTPBearerAuth

    host = host or config.host

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
    if org_name and not org_name.isspace():
        url = ORG_REPO_CREATE_URL.format(
            orgname=org_name,
        )

    res = s.post(urllib.parse.urljoin(host, url), data=data, auth=auth)

    if res.status_code != HTTPStatus.CREATED:
        logger.error(f"Response ({res.status_code}):\n" f"{res.content}")
        if res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            raise RuntimeError("Repository name is invalid or it already exists.")
        else:
            raise RuntimeError("Failed to create the desired repository.")

    repo = res.json()
    return Repo(
        owner=repo["owner"]["login"], name=repo["name"], token=token, branch="main"
    )


class Repo:
    def __init__(
        self, owner, name, username=None, password=None, token=None, branch=None
    ):

        """
        Repo class constructor. If branch is not provided, then default branch is used.

        :param owner (str): Store the username of the user who owns this repository
        :param name (str): Identify the repository
        :param username (str): Set the username to none if it is not provided
        :param password (str): Set the password to none if it is not provided
        :param token (str): Set the token
        :param branch (str): Set the branch to the default branch
        :return: The object of the class

        """
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

    def upload(
        self,
        local_path: Union[str, IOBase],
        commit_message=DEFAULT_COMMIT_MESSAGE,
        remote_path=None,
        **kwargs,
    ):
        """
        The upload function is used to upload files to the repository.
        It takes a file as an argument and logs the response status code and content.


        :param file (str): Specify the file to be uploaded
        :param commit_message (str): Specify a commit message
        :param path (str): Specify the path to upload the file to
        :param **kwargs: Pass in any additional parameters that are required for the upload function
        :return: None

        """
        if os.path.isdir(local_path):
            dir_to_upload = self.directory(remote_path)
            dir_to_upload.add_dir(local_path, commit_message=commit_message, **kwargs)
        else:
            file_to_upload = DataSet.get_file(local_path, remote_path)
            self.upload_files([file_to_upload], commit_message=commit_message, **kwargs)

    def upload_files(
        self,
        files,
        directory_path="",
        commit_message=DEFAULT_COMMIT_MESSAGE,
        versioning=None,
        new_branch=None,
        last_commit=None,
        force=False,
    ):
        """
        The upload_files function uploads a list of files to the specified directory.


        :param files (list(str)): Pass the files that are to be uploaded
        :param directory_path (str): Indicate the path of the directory in which we want to upload our files
        :param commit_message (str): Set the commit message
        :param versioning (str): Determine whether the files are uploaded to a new branch or not
        :param new_branch (str): Create a new branch
        :param last_commit (str): Tell the server that we want to upload a file without committing it
        :param force (bool): Force the upload of a file even if it is already present on the server
        :return: None
        """

        data = {
            "commit_choice": "direct",
            "commit_summary": commit_message,
            "versioning": versioning,
            "last_commit": last_commit,
            "is_dvc_dir": directory_path != "" and versioning != "git",
        }

        if new_branch is not None:
            data.update(
                {
                    "commit_choice": "commit-to-new-branch",
                    "new_branch_name": new_branch,
                }
            )

        if force:
            data["last_commit"] = self._get_last_commit()

        log_message(f'Uploading files ({len(files)}) to "{self.full_name}"...', logger)
        res = s.put(
            self.get_request_url(directory_path),
            data=data,
            files=[("files", file) for file in files],
            auth=self.auth,
            timeout=None,
        )
        self._log_upload_details(data, res, files)

    def _log_upload_details(self, data, res, files):
        """
        The _log_upload_details function logs the request URL, data, and files.
        It then logs the response status code and content. If the response is not 200(OK), it raises an error.



        :param data (str): Pass the data that will be uploaded to the server
        :param res (dict): Store the response from the server
        :param files (list(str)): Pass the files that are going to be uploaded
        :return: None

        """

        logger.debug(
            f"Request URL: {res.request.url}\n"
            f"Data:\n{json.dumps(data, indent=4)}\n"
            f"Files:\n{json.dumps(list(map(str, files)), indent=4)}"
        )

        if res.status_code != HTTPStatus.OK:
            raise determine_upload_api_error(res)
        else:
            log_message("Upload finished successfully!", logger)

    @property
    def auth(self):
        """
        The auth function is used to authenticate the user with the dagshub API.
            It takes in a username and password, or token as arguments. If both are provided,
            it will use the username and password combination to
            get a token from dagshub's authentication server.
            Otherwise, if only a token is provided it will be used for authentication.

        :return: The HTTPAuth object

        """
        if self.username is not None and self.password is not None:
            return httpx.BasicAuth(self.username, self.password)
        token = self.token or dagshub.auth.get_token()
        return HTTPBearerAuth(token)

    def directory(self, path):
        """
        The directory function returns a DataSet object that represents the directory at the given path.


        :param path (str): Specify the directory that will contain the data.
                           This directory is the "root" of the dataset.
        :return: A dataset object that represents the directory at the given path

        """
        return DataSet(self, path)

    def get_request_url(self, directory):
        """
        The get_request_url function returns the URL for uploading a file to DagsHub.

        :param directory (str): the path to a directory within this repo on DagsHub.
            For example, if you have created your repo in such a
            way that it has two directories named data and models,
            then you could pass one of these strings into this function as an argument.
        :return: The url for uploading a file

        """
        return urllib.parse.urljoin(
            self.src_url,
            CONTENT_UPLOAD_URL.format(
                owner=self.owner,
                reponame=self.name,
                branch=self.branch,
                path=urllib.parse.quote(directory, safe=""),
            ),
        )

    def _set_default_branch(self):

        """
        The _set_default_branch function is used to set the default branch for a repository.
        It first tries to get the default branch from DagsHub. If it fails, an error message is raised.

        :return: None
        """

        try:
            self.branch = helpers.get_default_branch(
                self.owner, self.name, self.auth, self.src_url
            )
        except Exception:
            raise RuntimeError(
                "Failed to get default branch for repository. "
                "Please specify a branch and make sure repository details are correct."
            )

    @property
    def full_name(self):
        """
        The full_name function returns the full name of a repository, meaning: "<owner>/<repo>"


        :return: The full name of a repository

        """

        return f"{self.owner}/{self.name}"

    def _get_last_commit(self):
        """
        The _get_last_commit function returns the last commit sha for a given branch.
        It is used to check if there are any new commits in the repo since we last ran our dag.

        :return: The commit id of the last commit for the branch
        """
        api_path = f"api/v1/repos/{self.full_name}/branches/{self.branch}"
        api_url = urllib.parse.urljoin(self.src_url, api_path)
        res = s.get(api_url, auth=self.auth)
        if res.status_code == HTTPStatus.OK:
            content = res.json()
            try:
                return content["commit"]["id"]
            except KeyError:
                logger.error(f"Cannot get commit sha for branch '{self.branch}'")
        return ""


class DataSet:
    def __init__(self, repo: Repo, directory: str):
        """

        :param repo (Repo object): Pass a repo object
        :param directory (str): Specify the directory of the repository
        :return: A DataSet object

        """

        self.files = {}
        self.repo = repo
        self.directory = self._clean_directory_name(directory)
        self.request_url = self.repo.get_request_url(directory)

    def add(self, file: Union[str, IOBase], path=None):
        """
        The add function adds a file to the list of files that will be uploaded.


        :param file (str): Specify the file to be uploaded
        :param path (str): Specify the path to upload the file
        :return: None

        """

        path, file = self.get_file(file, path)
        if file is not None:
            if path in self.files:
                log_message(
                    f'File already staged for upload on path "{path}". Overwriting', logger
                )
            self.files[path] = (path, file)

    def add_dir(self, local_path, glob_exclude="", commit_message=None, **upload_kwargs):
        """
        The add_dir function adds an entire dvc directory to a DagsHub repository.
        It does this by iterating through all the files in the given directory and uploading them one-by-one.
        The function also commits all of these changes at once, so as not to overload the API with requests.


        :param local_path  (str): Specify the local path where the dataset to upload is located
        :param glob_exclude (str): Exclude certain files from the upload process
        :param commit_message (str): Commit message
        :param upload_kwargs (dict): kwargs that are passed to the uploading function
        :return: None

        """

        file_counter = 0

        progress = rich.progress.Progress(rich.progress.SpinnerColumn(), *rich.progress.Progress.get_default_columns(),
                                          console=rich_console, transient=True, disable=config.quiet)
        total_task = progress.add_task("Uploading files...")

        with progress:
            for root, dirs, files in os.walk(local_path):
                folder_task = progress.add_task(f"Uploading files from {root}", total=len(files))

                if commit_message is None:
                    commit_message = upload_kwargs.get("commit_message", f"Commit data points in folder {root}")
                if "commit_message" in upload_kwargs:
                    del upload_kwargs["commit_message"]

                if len(files) > 0:
                    for filename in files:
                        rel_file_path = posixpath.join(root, filename)
                        rel_remote_file_path = rel_file_path.replace(local_path, "")
                        if (
                            glob_exclude == ""
                            or fnmatch.fnmatch(rel_file_path, glob_exclude) is False
                        ):
                            self.add(file=rel_file_path, path=rel_remote_file_path)
                            if len(self.files) > 49:
                                file_counter += len(self.files)
                                self.commit(commit_message, versioning="dvc", **upload_kwargs)
                                progress.update(folder_task, advance=len(self.files))
                                progress.update(total_task, completed=file_counter)
                    if len(self.files) > 0:
                        file_counter += len(self.files)
                        self.commit(commit_message, versioning="dvc", **upload_kwargs)
                        progress.update(total_task, completed=file_counter)
                progress.remove_task(folder_task)

        log_message(f"Directory upload complete, uploaded {file_counter} files", logger)

    @staticmethod
    def _clean_directory_name(directory: str):
        """
        The _clean_directory_name function takes a directory name as an argument
        and returns the normalized path of that directory.
        For example, if the input is ../../../ then it will return /. If the input is ./ then it will return ..
        If there are any other characters in the string,
        they will be ignored and only alphanumeric characters (a-zA-Z0-9)
        will be kept.

        :param directory (str): Specify the directory that will be cleaned
        :return: The normalized path of the directory
                 (The directory name with the path separator normalized to a forward slash)

        """

        return posixpath.normpath(directory)

    @staticmethod
    def get_file(file: Union[str, IOBase], path=None):
        """
        The get_file function is a helper function that takes in either a string or an IOBase object and returns
        a tuple containing the file's name and the file itself. If no path is provided, it will default to the name of
        the file.

        :param file (str):Union[str: Specify the file that you want to upload
        :param IOBase]: Handle both file paths and file objects
        :param path (str): Specify the path of the file
        :return: A tuple of the path and a file object

        """

        try:
            # if path is not provided, fall back to the file name
            if path is None:
                try:
                    path = posixpath.basename(
                        posixpath.normpath(file if type(file) is str else file.name)
                    )
                except Exception:
                    raise RuntimeError(
                        "Could not interpret your file's name. Please specify it in the keyword parameter 'path'."
                    )

            if type(file) is str:
                try:
                    f = open(file, "rb")
                    return path, f
                except IsADirectoryError:
                    raise IsADirectoryError(
                        "'file' must describe a file, not a directory."
                    )

            return path, file

        except Exception as e:
            logger.error(e)
            raise e

    def _reset_dataset(self):
        """
        The _reset_dataset function clears the files attribute of a Dataset object.

        :return: None
        """

        self.files.clear()

    def commit(self, commit_message=DEFAULT_COMMIT_MESSAGE, *args, **kwargs):
        """
        The commit function is used to commit the files in the dataset.
        It takes a commit message as an argument,
            if no argument is passed then it return default commit message "Upload files using DagsHub client".
        The function returns nothing.


        :param commit_message (str): Set the commit message
        :param *args: Pass a non-keyworded, variable-length argument list to the function
        :param **kwargs: Pass additional parameters to the function
        :return: None
        """

        file_list = list(self.files.values())
        self.repo.upload_files(
            file_list, self.directory, commit_message=commit_message, *args, **kwargs
        )
        self._reset_dataset()
