import fnmatch
import json
import logging
import os
import posixpath
import time
import urllib
from http import HTTPStatus
from io import IOBase
from pathlib import Path
from typing import Union, Tuple, BinaryIO, Dict, Optional, Any, List

import httpx
import rich.progress
import rich.status

import dagshub.auth
from dagshub.auth.token_auth import EnvVarDagshubToken
from dagshub.common import config, rich_console
from dagshub.common.api.repo import RepoAPI, BranchNotFoundError
from dagshub.common.helpers import log_message
from dagshub.upload.errors import determine_upload_api_error

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
FILES_UI_URL = "{owner}/{reponame}/src/{branch}/{path}"
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

FileUploadStruct = Tuple[os.PathLike, BinaryIO]


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
    :param auto_init (bool): Pass true to create an initial commit with README, .gitignore and LICENSE.
    :param gitignores (str): Which gitignore template(s) to use (comma separated string)
    :param license (str): Which license file to use
    :param readme (str): Readme file path to upload
    :param template (str): Which project template to use, options are: none, custom, notebook-template,
    cookiecutter-dagshub-dvc. To learn more, check out https://dagshub.com/docs/feature_guide/project_templates/
    :return: Repo object of the repository created
    """
    if template == "":
        template = "none"

    host = host or config.host

    username = config.username
    password = config.password
    token = None
    if username is not None and password is not None:
        auth = username, password
    else:
        auth = dagshub.auth.get_authenticator()
        token = auth.token_text

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
        owner=repo["owner"]["login"], name=repo["name"], username=username, password=password,
        token=token, branch="main"
    )


def validate_owner_repo(owner_repo: str) -> Tuple[str, str]:
    parts = owner_repo.split("/")
    if len(parts) != 2:
        raise ValueError("repo needs to be in the format <repo-owner>/<repo-name>")
    return parts[0], parts[1]


def upload_files(
    repo: str,
    local_path: Union[str, IOBase],
    commit_message=DEFAULT_COMMIT_MESSAGE,
    remote_path: str = None,
    **kwargs,
):
    """
    Convenience wrapper around Repo.upload
    :param repo: Repo identifier in the form <username>/<reponame>
    :param local_path: Specify the file or directory to be uploaded
    :param commit_message: Specify an optional commit message
    :param remote_path: Specify the path to upload the file to. Defaults to the relative path to the local_path.
    :param kwargs: Pass in any additional parameters that are required for the upload function
    """
    owner, repo = validate_owner_repo(repo)
    repo = Repo(owner, repo)
    repo.upload(local_path, commit_message=commit_message, remote_path=remote_path, **kwargs)


class Repo:
    def __init__(
        self, owner, name, username=None, password=None, token=None, branch=None
    ):

        """
        Repo class constructor. If branch is not provided, then default branch is used.

        WARNING: this class is not thread safe.
        Uploading files in parallel can lead to unexpected outcomes

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
        self.host = config.host

        self.username = username or config.username
        self.password = password or config.password
        self.token = token or config.token
        self.branch = branch

        self._api = RepoAPI(f"{owner}/{name}", host=self.host, auth=self.auth)

        # For mirror uploading: store the last revision for which we uploaded
        # When the last revision changes, that means the sync has been complete and we can upload a new batch
        self._last_upload_revision: Optional[str] = None
        self._last_upload_had_changes = False
        self._uploading_to_new_branch = False

        self.current_progress: Optional[rich.progress.Progress] = None

        if self.branch is None:
            logger.debug("Branch wasn't provided. Fetching default branch...")
            self.branch = self._api.default_branch
        logger.debug(f"Set branch: {self.branch}")

    def upload(
        self,
        local_path: Union[str, IOBase],
        commit_message=DEFAULT_COMMIT_MESSAGE,
        remote_path: str = None,
        **kwargs,
    ):
        """
        The upload function is used to upload files to the repository.
        It takes a file as an argument and logs the response status code and content.


        :param local_path: Specify the file to be uploaded
        :param commit_message: Specify a commit message
        :param remote_path: Specify the path to upload the file to
        :param **kwargs: Pass in any additional parameters that are required for the upload function
        :return: None

        """
        local_path = Path(local_path).resolve()
        if local_path.is_dir():
            if remote_path is None:
                try:
                    remote_path = local_path.relative_to(Path.cwd().resolve())
                except ValueError:
                    # local_path is outside cwd, use only its basename
                    remote_path = local_path.name
            remote_path = Path(remote_path).as_posix()
            dir_to_upload = self.directory(remote_path)
            dir_to_upload.add_dir(str(local_path), commit_message=commit_message, **kwargs)
        else:
            file_to_upload = DataSet.get_file(str(local_path), remote_path)
            self.upload_files([file_to_upload], commit_message=commit_message, **kwargs)

    def upload_files(
        self,
        files: List[FileUploadStruct],
        directory_path: str = "",
        commit_message: str = DEFAULT_COMMIT_MESSAGE,
        versioning: str = "auto",
        new_branch: str = None,
        last_commit: str = None,
        force: bool = False,
    ):
        """
        The upload_files function uploads a list of files to the specified directory.

        Args:
            files: List of Tuples of (path in repo, binaryIO) of files to upload
            directory_path: Directory in repo relative to which to upload files
            commit_message: Commit message
            versioning: Which versioning system to use to upload a file.
                Possible options: git, dvc, auto (best effort guess)
            new_branch: Create a new branch with the name of the passed argument
            last_commit: Consistency argument - last revision of the files you want to upgrade.
                Exists to prevent accidental overwrites
            force (bool): Force the upload of a file even if it is already present on the server.
                Sets last_commit to be the tip of the branch
        """

        # Truncate the commit message because the max we allow is 100 symbols
        commit_message = commit_message[:100]

        data = {
            "commit_choice": "direct",
            "commit_summary": commit_message,
            "versioning": versioning,
            "last_commit": last_commit,
            "is_dvc_dir": directory_path != "" and versioning != "git",
        }

        if self._api.is_mirror and new_branch is not None:
            # If not uploading to a new branch, and we're in a mirror - wait for the sync to complete
            self._poll_mirror_up_to_date()

        # Unset the new branch upload flag if it was set
        # (do that only after mirror poll so commit 2 on a new branch pushes correctly)
        if self._uploading_to_new_branch:
            self._uploading_to_new_branch = False

        upload_url = self.get_request_url(directory_path)

        try:
            self._last_upload_revision = self._api.last_commit_sha(self.branch)
        # New branch does not have a commit yet, so "last_upload_revision" will be None initially
        # NOTE: checking for new_branch is not enough, because it doesn't take into account
        # uploading to completely blank repos
        except BranchNotFoundError:
            self._uploading_to_new_branch = True
            log_message(
                f"Uploading to a new branch {self.branch}, "
                f"splitting it off from the default branch {self._api.default_branch}", logger)
            upload_url = self.get_request_url(directory=directory_path, branch=self._api.default_branch)
            new_branch = self.branch

        if new_branch is not None:
            data.update(
                {
                    "commit_choice": "commit-to-new-branch",
                    "new_branch_name": new_branch,
                }
            )

        if force:
            data["last_commit"] = self._last_upload_revision

        log_message(f'Uploading files ({len(files)}) to "{self._api.full_name}"...', logger)
        res = s.put(
            upload_url,
            data=data,
            files=[("files", file) for file in files],
            auth=self.auth,
            timeout=None,
        )
        self._log_upload_details(data, res, files)

        # The ETag header contains the hash of the uploaded commit,
        # check against the one we have to determine if anything changed
        if "ETag" in res.headers:
            new_tip = res.headers["ETag"]
            self._last_upload_had_changes = new_tip != self._last_upload_revision

    def _log_upload_details(self, data: Dict[str, Any], res: httpx.Response, files):
        """
        The _log_upload_details function debug logs the request URL, data, and files.
        It also prints for the user the status of their upload if it was successful
        If the response is 4xx/5xx it raises an error.

        Args:
            data: Executed request's body
            res: Server's response
            files: Uploaded file contents
        """

        logger.debug(
            f"Request URL: {res.request.url}\n"
            f"Data:\n{json.dumps(data, indent=4)}\n"
            f"Files:\n{json.dumps(list(map(str, files)), indent=4)}"
        )

        if res.status_code == HTTPStatus.OK:
            if "ETag" in res.headers:
                new_tip = res.headers["ETag"]
                if new_tip == self._last_upload_revision:
                    log_message("Upload successful, content was identical and no new commit was created", logger)
                    return
            log_message("Upload finished successfully!", logger)
        elif res.status_code == HTTPStatus.NO_CONTENT:
            log_message("Upload successful, content was identical and no new commit was created", logger)
        elif 200 < res.status_code < 300:
            log_message(f"Got unknown successful status code {res.status_code}")
        else:
            raise determine_upload_api_error(res)

    def _poll_mirror_up_to_date(self):
        """
        Synchronization lock for the mirrored repository uploading
        Since the upload is being done "through" DagsHub,
            and we rely on the change first showing up on the original repo, then being synced back to us,
            there is a possibility of uploading a new batch before the sync has been completed,
            during which the DagsHub repo is out of date with the original mirror.
        This is a client-side fix made to mitigate this.
        We poll for the change in the revision and compare it to the revision we had when we last uploaded
        When the revision changes, that means the sync has been completed and we can upload a new batch
        """
        if not self._api.is_mirror:
            return

        # Initial state - assume we can upload
        # Also can upload if last upload didn't have any changes
        if not self._uploading_to_new_branch and (
            self._last_upload_revision is None or not self._last_upload_had_changes):
            return

        poll_interval = 1.0  # seconds
        poll_timeout = 600.0
        start_time = time.time()

        if self.current_progress is not None:
            task = self.current_progress.add_task("Waiting for the mirror to sync", total=None)

            def finish():
                self.current_progress.remove_task(task)
        else:
            status = rich.status.Status("Waiting for the mirror to sync", console=rich_console)
            status.start()

            def finish():
                status.stop()

        while time.time() - start_time < poll_timeout:
            try:
                new_revision = self._api.last_commit_sha(self.branch)
            except BranchNotFoundError:
                # New branch that didn't get back to DagsHub yet
                time.sleep(poll_interval)
                continue
            if new_revision == self._last_upload_revision:
                time.sleep(poll_interval)
            else:
                finish()
                return

        finish()
        logger.warning(f"Timed out while polling for a mirror sync finishing after {poll_timeout} s. "
                       f"Trying to push anyway, which might not work.")

    @property
    def auth(self):
        """
        The auth function is used to authenticate the user with the dagshub API.
            Username and password take priority for authentication, then token.
            If none were provided, it goes through the usual token flow involving the token cache

        :return: The HTTPAuth object

        """
        if self.username is not None and self.password is not None:
            return httpx.BasicAuth(self.username, self.password)
        if self.token:
            return EnvVarDagshubToken(self.token)
        return dagshub.auth.get_authenticator()

    def directory(self, path):
        """
        The directory function returns a DataSet object that represents the directory at the given path.


        :param path (str): Specify the directory that will contain the data.
                           This directory is the "root" of the dataset.
        :return: A dataset object that represents the directory at the given path

        """
        return DataSet(self, path)

    def get_request_url(self, directory, branch=None):
        """
        The get_request_url function returns the URL for uploading a file to DagsHub.

        :param directory: the path to a directory within this repo on DagsHub.
            For example, if you have created your repo in such a
            way that it has two directories named data and models,
            then you could pass one of these strings into this function as an argument.
        :param branch: branch to which upload file.
            Default is None, which uses the branch set on object creation
        :return: The url for uploading a file

        """
        return self.get_repo_url(CONTENT_UPLOAD_URL, directory, branch)

    def get_files_ui_url(self, directory):
        """
        The get_files_ui_url function returns the URL for seeing the uploaded files on DagsHub.

        :param directory: the path to a directory within this repo on DagsHub.
            For example, if you have created your repo in such a
            way that it has two directories named data and models,
            then you could pass one of these strings into this function as an argument.
        :return: The url that you can navigate to in your browser to see the files

        """
        return self.get_repo_url(FILES_UI_URL, directory)

    def get_repo_url(self, url_format, directory, branch=None):
        if branch is None:
            branch = self.branch
        return urllib.parse.urljoin(
            self.host,
            url_format.format(
                owner=self.owner,
                reponame=self.name,
                branch=branch,
                path=urllib.parse.quote(directory, safe=""),
            ),
        )


class DataSet:
    def __init__(self, repo: Repo, directory: str):
        """

        :param repo (Repo object): Pass a repo object
        :param directory (str): Specify the directory of the repository
        :return: A DataSet object

        """

        self.files: Dict[os.PathLike, Tuple[os.PathLike, BinaryIO]] = {}
        self.repo = repo
        self.directory = self._clean_directory_name(directory)

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
        upload_file_number = 100
        file_counter = 0

        progress = rich.progress.Progress(rich.progress.SpinnerColumn(), *rich.progress.Progress.get_default_columns(),
                                          rich.progress.MofNCompleteColumn(),
                                          console=rich_console, transient=True, disable=config.quiet)
        total_task = progress.add_task("Uploading files...", total=None)
        self.repo.current_progress = progress

        # If user hasn't specified versioning, then assume we're uploading dvc (this makes most sense for folders)
        if "versioning" not in upload_kwargs:
            upload_kwargs["versioning"] = "dvc"

        try:
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
                                if len(self.files) >= upload_file_number:
                                    file_counter += len(self.files)
                                    self.commit(commit_message, **upload_kwargs)
                                    progress.update(folder_task, advance=len(self.files), refresh=True)
                                    progress.update(total_task, completed=file_counter, refresh=True)
                        if len(self.files) >= upload_file_number:
                            file_counter += len(self.files)
                            self.commit(commit_message, **upload_kwargs)
                            progress.update(folder_task, advance=len(self.files), refresh=True)
                            progress.update(total_task, completed=file_counter, refresh=True)
                    progress.remove_task(folder_task)

                if len(self.files) > 0:
                    file_counter += len(self.files)
                    self.commit(commit_message, **upload_kwargs)
                    progress.update(total_task, completed=file_counter)

            log_message(f"Directory upload complete, uploaded {file_counter} files"
                        f" to {self.repo.get_files_ui_url(self.directory)}", logger)
        finally:
            self.repo.current_progress = None

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
    def get_file(file: Union[str, IOBase], path: os.PathLike = None) -> FileUploadStruct:
        """
        The get_file function is a helper function that takes in either a string or an IOBase object and returns
        a tuple containing the file's name and the file itself. If no path is provided, it will default to the name of
        the file.

        :param file (Union[str, IOBase]): File to upload
        :param path (str): Desired path of the file in the repository
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
            raise

    def _reset_dataset(self):
        """
        The _reset_dataset function clears the files attribute of a Dataset object.

        :return: None
        """
        for f in self.files.values():
            try:
                f[1].close()
            except Exception as e:
                logger.warning(f"Error closing file {f[0]}: {e}")
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
