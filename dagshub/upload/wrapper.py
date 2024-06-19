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
from concurrent.futures import ThreadPoolExecutor

import httpx
import rich.progress
import rich.status
from tenacity import retry, retry_if_exception_type, wait_fixed, stop_after_attempt

import dagshub.auth
from dagshub.auth.token_auth import EnvVarDagshubToken
from dagshub.common import config, rich_console
from dagshub.common.api.repo import RepoAPI, BranchNotFoundError
from dagshub.common.helpers import log_message
from dagshub.upload.errors import determine_upload_api_error, InternalServerErrorError
from dagshub.common.rich_util import get_rich_progress
from dagshub.repo_bucket import get_repo_bucket_client

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
FILES_UI_URL = "{owner}/{reponame}/src/{branch}/{path}"
DEFAULT_COMMIT_MESSAGE = "Upload files using DagsHub client"
DEFAULT_DATASET_COMMIT_MESSAGE = "Initial dataset commit"
REPO_CREATE_URL = "api/v1/user/repos"
ORG_REPO_CREATE_URL = "api/v1/org/{orgname}/repos"
USER_INFO_URL = "api/v1/user"
DEFAULT_DATA_DIR_NAME = "data"
logger = logging.getLogger(__name__)

s = httpx.Client()
s.timeout = config.http_timeout
s.follow_redirects = True
s.headers.update(config.requests_headers)

FileUploadStruct = Tuple[os.PathLike, BinaryIO]


def create_dataset(repo_name: str, local_path: str, glob_exclude: str = "", org_name: str = "", private=False):
    """
    Create a new repository on DagsHub and upload an entire folder dataset to it

    Args:
        repo_name: Name of the repository to be created.
        local_path: local path where the dataset to upload is located.
        glob_exclude: glob pattern to exclude certain files from being uploaded.
        org_name (optional): Organization that will own the repo. Alternative to creating a repository owned by you.
        private: Set to ``True`` to make the repository private.

    Returns:
        :class:`.Repo`: Repo object of the repository created.
    """
    repo = create_repo(repo_name, org_name=org_name, private=private)
    dir = repo.directory(repo_name)
    dir.add_dir(local_path, glob_exclude, commit_message=DEFAULT_DATASET_COMMIT_MESSAGE)
    return repo


def add_dataset_to_repo(repo: "Repo", local_path: str, data_dir: str = DEFAULT_DATA_DIR_NAME):
    """
    Given a repository created on dagshub - upload a dataset folder into it

    Args:
        repo: repository created beforehand
        local_path: local path where the dataset to upload is located
        data_dir: name of data directory that will be created inside repo
    """
    dir = repo.directory(data_dir)
    dir.add_dir(local_path, commit_message=DEFAULT_DATASET_COMMIT_MESSAGE)


def create_repo(
    repo_name: str,
    org_name: str = "",
    description: str = "",
    private: bool = False,
    auto_init: bool = False,
    gitignores: str = "Python",
    license: str = "",
    readme: str = "",
    template: str = "custom",
    host: str = "",
):
    """
    Creates a repository on DagsHub for the current user or an organization passed as an argument

    Args:
        repo_name: Name of the repository to be created.
        org_name (optional): Organization that will own the repo. Alternative to creating a repository owned by you.
        description: Repository description.
        private: Set to ``True`` to make repository private.
        auto_init: Set to True to create an initial commit with README, .gitignore and LICENSE.
        gitignores: Which gitignore template(s) to use in a comma separated string.
        license: Which license file to use.
        readme: Readme template to initialize with.
        template: Which project template to use, options are:

            - ``"none"`` - creates an empty repo
            - ``"custom"`` - creates a repo with your specified ``gitignores``, ``license`` and ``readme``
            - ``"notebook-template"``
            - ``"cookiecutter-mlops"``
            - ``"cookiecutter-dagshub-dvc"``

            By default, creates an empty repo if none of ``gitignores``, ``license`` or ``readme`` were provided.
            Otherwise, the template is ``"custom"``.

        host: URL of the DagsHub instance to host the repo on.

    .. note::
        To learn more about the templates, visit https://dagshub.com/docs/feature_guide/project_templates/

    Returns:
        :class:`.Repo`: Repo object of the repository created.
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
        owner=repo["owner"]["login"],
        name=repo["name"],
        username=username,
        password=password,
        token=token,
        branch="main",
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
    bucket: bool = False,
    **kwargs,
):
    """
    Upload file(s) into a repository.

    Args:
        repo: Repo name in the form of ``<username>/<reponame>``.
        local_path: File or directory to be uploaded.
        commit_message (optional): Specify a commit message.
        remote_path: Specify the path to upload the file to.\
        Defaults to the relative component of ``local_path`` to CWD.
        bucket: Upload the file(s) to the DagsHub Storage bucket

    For kwarg docs look at :func:`Repo.upload() <dagshub.upload.Repo.upload>`.
    """
    owner, repo = validate_owner_repo(repo)
    repo = Repo(owner, repo)
    repo.upload(local_path, commit_message=commit_message, remote_path=remote_path, bucket=bucket, **kwargs)


def upload_file_to_s3(s3_client, local_path, bucket_name, remote_path, progress=None, task=None):
    """
    Upload a single file to S3.

    :param s3_client: An instance of boto3 S3 client
    :param local_path: The local path to the file
    :param bucket_name: The S3 bucket name
    :param remote_path: The S3 path where the file will be uploaded
    :param progress: (rich.progress.Progress, optional) A Rich library Progress instance for visual progress tracking.
    If provided, `task_id` must also be given. Default is None.
    :param task: The task ID associated with this upload task in the Rich Progress instance.
    Required if `progress` is provided. Default is None.
    """
    s3_client.upload_file(local_path, bucket_name, remote_path)
    if progress is not None and task is not None:
        progress.update(task, advance=1)
    else:
        log_message(f"Uploaded {local_path} to s3://{bucket_name}/{remote_path}")


class Repo:
    def __init__(
        self,
        owner: str,
        name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        branch: Optional[str] = None,
    ):
        """
        Class that can be used to upload files into a repository on DagsHub

        .. warning::
            This class is not thread safe.
            Uploading files in parallel can lead to unexpected outcomes

        Args:
            owner: user or org that owns the repository.
            name: name of the repository.
            token (optional): Token to use for authentication. If unset, uses the cached token or goes through OAuth.
            username: Username to log in with (alternative to token).
            password: Password to log in with (alternative to token).
            branch: Branch to upload files to.
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
        bucket: bool = False,
        **kwargs,
    ):
        """
        Upload a file or a directory to the repo.

        Args:
            local_path: Path to file or directory to be uploaded
            commit_message: Specify a commit message
            remote_path: Specify the path to upload the file/dir to.
                If unspecified, sets the value to the relative component of ``local_path`` to CWD.
                If ``local_path`` is not relative to CWD, ``remote_path`` is the last component of the ``local_path``
            bucket: Upload to the DagsHub Storage bucket (s3-compatible) without versioning, if this is set to true,
            commit_message will be ignored.

        The kwargs are the parameters of :func:`upload_files`
        """
        if commit_message is None:
            commit_message = DEFAULT_COMMIT_MESSAGE
        local_path = Path(local_path).resolve()
        if local_path.is_dir():
            if remote_path is None:
                try:
                    remote_path = local_path.relative_to(Path.cwd().resolve())
                except ValueError:
                    # local_path is outside cwd, use only its basename
                    remote_path = local_path.name
            remote_path = Path(remote_path).as_posix()
            if bucket:
                self.upload_files_to_bucket(local_path, remote_path, **kwargs)
            else:
                dir_to_upload = self.directory(remote_path)
                dir_to_upload.add_dir(str(local_path), commit_message=commit_message, **kwargs)
        else:
            if bucket:
                self.upload_files_to_bucket(local_path, remote_path, **kwargs)
            else:
                file_to_upload = DataSet.get_file(str(local_path), remote_path)
                self.upload_files([file_to_upload], commit_message=commit_message, **kwargs)

    @retry(retry=retry_if_exception_type(InternalServerErrorError), wait=wait_fixed(3), stop=stop_after_attempt(5))
    def upload_files(
        self,
        files: List[FileUploadStruct],
        directory_path: str = "",
        commit_message: Optional[str] = DEFAULT_COMMIT_MESSAGE,
        versioning: str = "auto",
        new_branch: str = None,
        last_commit: str = None,
        force: bool = False,
        quiet: bool = False,
    ):
        """
        Upload a list of binary files to the specified directory.
        This function is lower level than :func:`upload`,
        but useful when you don't have the files stored on the filesystem.

        Args:
            files: List of Tuples of (path in repo, binaryIO) of files to upload
            directory_path: Directory in repo relative to which to upload files
            commit_message: Commit message
            versioning: Which versioning system to use to upload a file.
                Possible options: ``"git"``, ``"dvc"``, ``"auto"`` (default, best effort guess)
            new_branch: Create a new branch with this name
            last_commit: Consistency argument - last revision of the files you want to commit on top of.
                Exists to prevent accidental overwrites of data.
            force (bool): Force the upload of a file even if it is already present on the server.
                Sets last_commit to be the tip of the branch
            quiet (bool): Don't show messages about starting/successfully completing an upload.
                Set to True when uploading a directory
        """

        if commit_message is None:
            commit_message = DEFAULT_COMMIT_MESSAGE

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
                f"splitting it off from the default branch {self._api.default_branch}",
                logger,
            )
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

        if not quiet:
            log_message(f'Uploading files ({len(files)}) to "{self._api.full_name}"...', logger)
        res = s.put(
            upload_url,
            data=data,
            files=[("files", file) for file in files],
            auth=self.auth,
            timeout=None,
        )
        self._log_upload_details(data, res, files, quiet)

        # The ETag header contains the hash of the uploaded commit,
        # check against the one we have to determine if anything changed
        if "ETag" in res.headers:
            new_tip = res.headers["ETag"]
            self._last_upload_had_changes = new_tip != self._last_upload_revision

    def _log_upload_details(self, data: Dict[str, Any], res: httpx.Response, files, quiet: bool):
        """
        The _log_upload_details function debug logs the request URL, data, and files.
        It also prints for the user the status of their upload if it was successful
        If the response is 4xx/5xx it raises an error.

        Args:
            data: Executed request's body
            res: Server's response
            files: Uploaded file contents
            quiet: Log successful upload
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
            if not quiet:
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
            self._last_upload_revision is None or not self._last_upload_had_changes
        ):
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
        logger.warning(
            f"Timed out while polling for a mirror sync finishing after {poll_timeout} s. "
            f"Trying to push anyway, which might not work."
        )

    @property
    def auth(self):
        """
        The auth function is used to authenticate the user with the dagshub API.
            Username and password take priority for authentication, then token.
            If none were provided, it goes through the usual token flow involving the token cache

        :return: The HTTPAuth object

        :meta private:
        """
        if self.username is not None and self.password is not None:
            return httpx.BasicAuth(self.username, self.password)
        if self.token:
            return EnvVarDagshubToken(self.token)
        return dagshub.auth.get_authenticator()

    def directory(self, path: str) -> "DataSet":
        """
        Create a :class:`~dagshub.upload.wrapper.DataSet` object that allows you to stage multiple files before\
        pushing them all to DagsHub in a single commit with :func:`~dagshub.upload.wrapper.DataSet.commit`.

        Args:
            path: The path of the directory in the repository relative to which the files will be uploaded.
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

        :meta private:
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

        :meta private:
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

    def upload_files_to_bucket(self, local_path, remote_path, max_workers=config.upload_threads, **kwargs):
        """
        Upload a file or directory to an S3 bucket, preserving the directory structure.

        :param local_path: Path to the local directory to upload
        :param remote_path: The directory path within the S3 bucket
        :param max_workers: The maximum number of threads to use
        """

        s3 = get_repo_bucket_client(self._api.full_name)
        if remote_path.split("/")[0] == self.name:
            remote_path = remote_path.split("/", 1)[1]
        if local_path.is_file():
            upload_file_to_s3(s3_client=s3, local_path=local_path, bucket_name=self.name, remote_path=remote_path)
        else:
            upload_tasks = []
            # Walk through the local directory
            for root, dirs, files in os.walk(local_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, local_path)
                    s3_path = os.path.join(remote_path, relative_path)
                    s3_path = s3_path.replace(os.path.sep, "/")  # Ensure correct path separator for S3
                    upload_tasks.append((file_path, s3_path))

            # Use ThreadPoolExecutor to upload files in parallel
            progress = get_rich_progress(rich.progress.MofNCompleteColumn(), transient=False)
            task_id = progress.add_task("Uploading files...", total=len(upload_tasks))

            with progress:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(
                            upload_file_to_s3,
                            s3_client=s3,
                            local_path=task[0],
                            bucket_name=self.name,
                            remote_path=task[1],
                            progress=progress,
                            task=task_id,
                        )
                        for task in upload_tasks
                    ]
                    for future in futures:
                        future.result()  # Wait for all futures to complete


class DataSet:
    """
    Not to be confused with DataEngine's datasets.
    This class represents a folder with files that are going to be uploaded to a repo.
    """

    def __init__(self, repo: Repo, directory: str):
        self.files: Dict[os.PathLike, Tuple[os.PathLike, BinaryIO]] = {}
        self.repo = repo
        self.directory = self._clean_directory_name(directory)

    def add(self, file: Union[str, IOBase], path=None):
        """
        Add a file to upload. The file will not be uploaded unless you call :func:`commit`

        Args:
            file: Path to the file on the filesystem OR the contents of the file.
            path: Where to store the file in the repo.
        """

        path, file = self.get_file(file, path)
        if file is not None:
            if path in self.files:
                log_message(f'File already staged for upload on path "{path}". Overwriting', logger)
            self.files[path] = (path, file)

    def add_dir(self, local_path, glob_exclude="", commit_message=None, **upload_kwargs):
        """
        Add *and upload* an entire directory to the DagsHub repository.

        By default, this uploads a dvc folder.

        Args:
            local_path: Local path of the directory to upload.
            glob_exclude: Glob pattern to exclude some files from being uploaded.
            commit_message: Message of the commit with the upload.

        The keyword arguments are passed to :func:`Repo.upload_files() <dagshub.upload.Repo.upload_files>`.
        """
        upload_file_number = 100
        max_batch_file_size = 100 * 1024 * 1024
        file_counter = 0

        total_num_files = 0
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                rel_file_path = posixpath.join(root, filename)
                if glob_exclude == "" or fnmatch.fnmatch(rel_file_path, glob_exclude) is False:
                    total_num_files += 1

        progress = rich.progress.Progress(
            rich.progress.SpinnerColumn(),
            *rich.progress.Progress.get_default_columns(),
            rich.progress.MofNCompleteColumn(),
            console=rich_console,
            transient=True,
            disable=config.quiet,
        )
        total_task = progress.add_task("Uploading files...", total=total_num_files)
        self.repo.current_progress = progress

        # If user hasn't specified versioning, then assume we're uploading dvc (this makes most sense for folders)
        if "versioning" not in upload_kwargs:
            upload_kwargs["versioning"] = "dvc"

        upload_kwargs["quiet"] = True

        try:
            with progress:
                for root, dirs, files in os.walk(local_path):
                    if len(files) == 0:
                        continue

                    folder_task = progress.add_task(f"Uploading files from {root}", total=len(files))

                    if commit_message is None:
                        commit_message = upload_kwargs.get("commit_message", f"Commit data points in folder {root}")
                    if "commit_message" in upload_kwargs:
                        del upload_kwargs["commit_message"]

                    file_batches = []
                    current_file_batch = []
                    current_batch_file_size = 0

                    for filename in files:
                        rel_file_path = posixpath.join(root, filename)
                        if glob_exclude == "" or fnmatch.fnmatch(rel_file_path, glob_exclude) is False:
                            current_file_batch.append(rel_file_path)
                            current_batch_file_size += os.path.getsize(rel_file_path)

                            if (
                                len(current_file_batch) >= upload_file_number
                                or current_batch_file_size >= max_batch_file_size
                            ):
                                file_batches.append(current_file_batch)
                                current_file_batch = []
                                current_batch_file_size = 0

                    if current_file_batch:
                        file_batches.append(current_file_batch)

                    for batch in file_batches:
                        for rel_file_path in batch:
                            rel_remote_file_path = rel_file_path.replace(local_path, "")
                            self.add(file=rel_file_path, path=rel_remote_file_path)

                        file_counter += len(self.files)
                        self.commit(commit_message, **upload_kwargs)
                        progress.update(folder_task, advance=len(batch), refresh=True)
                        progress.update(total_task, completed=file_counter, refresh=True)

                    progress.remove_task(folder_task)

            log_message(
                f"Directory upload complete, uploaded {file_counter} files"
                f" to {self.repo.get_files_ui_url(self.directory)}",
                logger,
            )
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

        :param directory: Specify the directory that will be cleaned
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

        :param file: File to upload
        :param path: Desired path of the file in the repository
        :return: A tuple of the path and a file object

        :meta private:
        """

        try:
            # if path is not provided, fall back to the file name
            if path is None:
                try:
                    path = posixpath.basename(posixpath.normpath(file if type(file) is str else file.name))
                except Exception:
                    raise RuntimeError(
                        "Could not interpret your file's name. Please specify it in the keyword parameter 'path'."
                    )

            if type(file) is str:
                try:
                    f = open(file, "rb")
                    return path, f
                except IsADirectoryError:
                    raise IsADirectoryError("'file' must describe a file, not a directory.")

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
        Commit files added with :func:`add` to the repo

        Args:
            commit_message: Message of the commit with the upload.

        Other positional and keyword arguments are passed to
        :func:`Repo.upload_files() <dagshub.upload.Repo.upload_files>`
        """

        file_list = list(self.files.values())
        self.repo.upload_files(file_list, self.directory, commit_message=commit_message, *args, **kwargs)
        self._reset_dataset()
