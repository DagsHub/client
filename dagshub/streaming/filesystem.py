import builtins
import importlib
import io
import logging
import os
import re
import subprocess
import sys
from configparser import ConfigParser
from functools import wraps, cached_property
from multiprocessing import AuthenticationError
from os import PathLike
from pathlib import Path, PurePosixPath
from typing import Optional, TypeVar, Union, Dict, Set, Tuple, List, Any, Callable
from urllib.parse import urlparse, ParseResult

import dacite
from httpx import Response
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential, before_sleep_log, RetryError

from dagshub.common import config, is_inside_notebook, is_inside_colab
from dagshub.common.api.repo import RepoAPI, CommitNotFoundError
from dagshub.common.api.responses import ContentAPIEntry, StorageContentAPIResult
from dagshub.common.helpers import http_request, get_project_root, log_message
from dagshub.streaming.dataclasses import DagshubPath
from dagshub.streaming.errors import FilesystemAlreadyMountedError

# Pre 3.11 - need to patch _NormalAccessor for _pathlib, because it pre-caches open and other functions.
# In 3.11 _NormalAccessor was removed
PRE_PYTHON3_11 = sys.version_info.major == 3 and sys.version_info.minor < 11
if PRE_PYTHON3_11:
    from pathlib import _NormalAccessor as _pathlib  # noqa: E402


T = TypeVar("T")
logger = logging.getLogger(__name__)


def wrapreturn(wrappertype):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return wrappertype(func(*args, **kwargs))

        return wrapper

    return decorator


class dagshub_ScandirIterator:
    def __init__(self, iterator):
        self._iterator = iterator

    def __iter__(self):
        return self._iterator

    def __next__(self):
        return self._iterator.__next__()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self


SPECIAL_FILE = Path(".dagshub-streaming")


def _is_server_error(resp: Response):
    return resp.status_code >= 500


# TODO: Singleton metaclass that lets us keep a "main" DvcFilesystem instance
class DagsHubFilesystem:
    """
    A DagsHub-repo aware filesystem class

    :param project_root: Path to the git repository with the repo.
        If None, traverse up the filesystem from the current dir until we find a git repo
    :param repo_url: URL to the DagsHub repository.
        If None, URL is received from the git configuration
    :param branch: Explicitly sets a branch/commit revision to work with
        If None, branch is received from the git configuration
    :param token: DagsHub API token
    :param username: DagsHub username (as an alternative to using the token)
    :param password: DagsHub password (as an alternative to using the token)
    :param timeout: Timeout in seconds for HTTP requests.
        Influences all requests except for file download, which has no timeout
    :param exclude_globs: One or more glob patterns to exclude from looking up on the server
        This is useful in case your framework tries to look up cached files on disk that might not be there.
        Example: YOLO and .npy files
    :param frameworks: List of frameworks that need custom patched openers.
        Right now the following is supported:

        - ``transformers`` - patches ``safetensors``
    """

    already_mounted_filesystems: Dict[Path, "DagsHubFilesystem"] = {}
    hooked_instance: Optional["DagsHubFilesystem"] = None

    # Framework-specific override functions.
    # These functions will be patched with a function that calls fs.open() before calling the original function
    # Classes are marked by $, so if you need to change a static/class method, use module.$class.func
    _framework_override_map: Dict[str, List[str]] = {
        "transformers": ["safetensors.safe_open", "tokenizers.$Tokenizer.from_file"],
    }

    def __init__(
        self,
        project_root: Optional["PathLike | str"] = None,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
        exclude_globs: Optional[Union[List[str], str]] = None,
        frameworks: Optional[List[str]] = None,
    ):
        # Find root directory of Git project
        if not project_root:
            try:
                self.project_root = get_project_root(Path(os.path.abspath(".")))
            except ValueError:
                raise ValueError(
                    "Could not find a git repo. Either run the function inside of a git repo, "
                    "specify `project_root` with the path to a cloned DagsHub repository, "
                    "or specify `repo_url` (url of repo on DagsHub) and "
                    "`project_root` (path to the folder where to mount the filesystem) arguments"
                )

        else:
            self.project_root = Path(os.path.abspath(project_root))
        del project_root
        # TODO: if no Git project found, search for .dvc project?

        if not repo_url:
            remotes = self.get_remotes_from_git_config()
            if len(remotes) > 0:
                repo_url = remotes[0]
            else:
                raise ValueError("No DagsHub git remote detected, please specify repo_url= argument or --repo_url flag")

        self.user_specified_branch = branch
        self.parsed_repo_url = urlparse(repo_url)
        # Key: path, value: dict of {name, type} on that path (in remote)
        self.remote_tree: Dict[str, Dict[str, str]] = {}
        self.frameworks = frameworks

        # Determine if any authentication is needed
        self.username = username or config.username
        self.password = password or config.password
        self.token = token or config.token
        self.timeout = timeout or config.http_timeout

        if exclude_globs is None:
            exclude_globs = []
        elif exclude_globs is str:
            exclude_globs = [exclude_globs]

        self.exclude_globs: List[str] = exclude_globs

        self._listdir_cache: Dict[str, Optional[Tuple[List[ContentAPIEntry], bool]]] = {}

        self._api = self._generate_repo_api(self.parsed_repo_url)

        self.check_project_root_use()

        # Check that the repo is accessible by accessing the content root
        response = self._api_listdir(DagshubPath(self, self.project_root, Path(), Path()))
        if response is None:
            # TODO: Check .dvc/config{,.local} for credentials
            raise AuthenticationError("DagsHub credentials required, however none provided or discovered")

        self._storages = self._api.get_connected_storages()

    def _generate_repo_api(self, repo_url: ParseResult) -> RepoAPI:
        host = f"{repo_url.scheme}://{repo_url.netloc}"
        repo = repo_url.path
        return RepoAPI(repo=repo, host=host, auth=self.auth)

    @cached_property
    def _current_revision(self) -> str:
        """
        Gets current revision on repo:
        - If User specified a branch, returns HEAD of that brunch on the remote
        - If branch wasn't detected, returns HEAD of default branch in the speficied remote.
        - If HEAD is a branch, tries to find a dagshub remote associated with it and get its HEAD
        - If HEAD is a commit revision, checks that the commit exists on DagsHub
        """

        if self.user_specified_branch:
            branch = self.user_specified_branch
        else:
            try:
                with open(self.project_root / ".git/HEAD") as head_file:
                    head = head_file.readline().strip()
                if head.startswith("ref"):
                    branch = head.split("/")[-1]
                else:
                    # contents of HEAD is the revision - check that this commit exists on remote
                    if self.is_commit_on_remote(head):
                        return head
                    else:
                        raise RuntimeError(
                            f"Current HEAD ({head}) doesn't exist on the remote. "
                            f"Please push your changes to the remote or checkout a tracked branch."
                        )

            except FileNotFoundError:
                logger.debug(
                    "Couldn't get branch info from local git repository, "
                    + "fetching default branch from the remote..."
                )
                branch = self._api.default_branch

        # check if it is a commit sha, in that case do not load the sha
        sha_regex = re.compile(r"^([a-f0-9]){5,40}$")
        if sha_regex.match(branch):
            try:
                self._api.get_commit_info(branch)
                return branch
            except CommitNotFoundError:
                pass

        return self._api.last_commit_sha(branch)

    def is_commit_on_remote(self, sha1):
        try:
            self._api.get_commit_info(sha1)
            return True
        except CommitNotFoundError:
            return False

    def check_project_root_use(self):
        """
        Checks that there's no other filesystem being mounted at the current project root
        If there is one, throw an error

        :meta private:
        """

        def is_subpath(a: Path, b: Path) -> bool:
            # Checks if either a or b are subpaths of each other
            a_str = a.as_posix()
            b_str = b.as_posix()
            return a_str.startswith(b_str) or b_str.startswith(a_str)

        for p, f in DagsHubFilesystem.already_mounted_filesystems.items():
            if is_subpath(p, self.project_root):
                raise FilesystemAlreadyMountedError(self.project_root, f.parsed_repo_url.path[1:], f._current_revision)

        DagsHubFilesystem.already_mounted_filesystems[self.project_root] = self

    def get_remote_branch_head(self, branch):
        """
        Get the head commit ID of a remote branch.

        Args:
            branch (str): The name of the remote branch.

        Raises:
            RuntimeError: Raised if there is an issue when trying to get the head of the branch.

        Returns:
            str: The commit ID of the head of the remote branch.

        :meta private:
        """
        url = self.get_api_url(f"/api/v1/repos{self.parsed_repo_url.path}/branches/{branch}")
        resp = self.http_get(url)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Got status {resp.status_code} while trying to get head of branch {branch}. \r\n"
                f"Response body: {resp.content}"
            )
        return resp.json()["commit"]["id"]

    @property
    def auth(self):
        import dagshub.auth

        if self.username is not None and self.password is not None:
            return self.username, self.password

        try:
            return dagshub.auth.get_authenticator()
        except dagshub.auth.OauthNonInteractiveShellException:
            logger.debug("Failed to perform OAuth in a non interactive shell")

        # Try to fetch credentials from the git credential file
        proc = subprocess.run(["git", "credential", "fill"], input=f"url={self.repo_url}".encode(), capture_output=True)
        answer = {line[: line.index("=")]: line[line.index("=") + 1 :] for line in proc.stdout.decode().splitlines()}
        if "username" in answer and "password" in answer:
            return answer["username"], answer["password"]

    def get_remotes_from_git_config(self) -> List[str]:
        """
        Get the list of DagsHub remotes from the Git configuration.

        Returns:
            List[str]: A list of DAGsHub remote URLs.

        :meta private:
        """
        # Get URLs of dagshub remotes
        git_config = ConfigParser()
        git_config.read(Path(self.project_root) / ".git/config")
        git_remotes = [urlparse(git_config[remote]["url"]) for remote in git_config if remote.startswith("remote ")]
        res_remotes = []
        for remote in git_remotes:
            if remote.hostname != config.hostname:
                continue
            remote = remote._replace(netloc=remote.hostname)
            remote = remote._replace(path=re.compile(r"(\.git)?/?$").sub("", remote.path))
            res_remotes.append(remote.geturl())
        return res_remotes

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        # Remove from map of mounted filesystems
        if hasattr(self, "project_root") and self.project_root in DagsHubFilesystem.already_mounted_filesystems:
            DagsHubFilesystem.already_mounted_filesystems.pop(self.project_root)

    def _parse_path(self, file: Union[str, PathLike, int]) -> DagshubPath:
        orig_path = Path(file)
        if isinstance(file, int):
            return DagshubPath(self, None, None, orig_path)
        if file == "":
            return DagshubPath(self, None, None, orig_path)
        abspath = Path(os.path.abspath(file))
        try:
            relpath = abspath.relative_to(os.path.abspath(self.project_root))
            if str(relpath).startswith("<"):
                return DagshubPath(self, abspath, None, orig_path)
            return DagshubPath(self, abspath, relpath, orig_path)
        except ValueError:
            return DagshubPath(self, abspath, None, orig_path)

    def _special_file(self):
        # TODO Include more information in this file
        return b"v0\n"

    def open(self, file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/functions.html#open)

        Open a file for reading or writing, with support for special files and DagsHub integration.

        Args:
            file (Union[str, int, bytes]): The file to be opened.
                It can be a path (str), file descriptor (int), or bytes-like object.
            mode (str, optional): The mode in which the file should be opened. Defaults to 'r'.
            buffering (int, optional): The buffering value. Defaults to -1.
            encoding (str, optional): The encoding to use when reading the file. Defaults to None.
            errors (str, optional): The error handling strategy. Defaults to None.
            newline (str, optional): The newline parameter. Defaults to None.
            closefd (bool, optional): Whether to close the file descriptor. Defaults to True.
            opener (callable, optional): The file opener. Defaults to None.

        Returns:
            File object: A file object representing the opened file.

        :meta private:
        """
        # FD passthrough
        if type(file) is int:
            return self.__open(file, mode, buffering, encoding, errors, newline, closefd)

        if type(file) is bytes:
            file = os.fsdecode(file)
        path = self._parse_path(file)
        if path.is_in_repo:
            if opener is not None:
                raise NotImplementedError("DagsHub's patched open() does not support custom openers")
            if path.is_passthrough_path:
                return self.__open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)
            elif path.relative_path == SPECIAL_FILE:
                return io.BytesIO(self._special_file())
            else:
                try:
                    return self.__open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)
                except FileNotFoundError as err:
                    # Open for reading - try to download the file
                    if "r" in mode:
                        try:
                            resp = self._api_download_file_git(path)
                        except RetryError:
                            raise RuntimeError(f"Couldn't download {path.relative_path} after multiple attempts")
                        if resp.status_code < 400:
                            self._mkdirs(path.absolute_path.parent)
                            # TODO: Handle symlinks
                            with self.__open(path.absolute_path, "wb") as output:
                                output.write(resp.content)
                            return self.__open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)
                        elif resp.status_code == 404:
                            raise FileNotFoundError(f"Error finding {path.relative_path} in repo or on DagsHub")
                        else:
                            raise RuntimeError(
                                f"Got response code {resp.status_code} from DagsHub while downloading file"
                                f" {path.relative_path}"
                            )
                    # Write modes - make sure that the folder is a tracked folder (create if doesn't exist on disk),
                    # and then let the user write to file
                    else:
                        try:
                            # Using the fact that stat creates tracked dirs (but still throws on nonexistent dirs)
                            _ = self.stat(path.absolute_path.parent)
                        except FileNotFoundError:
                            raise err
                        # Try to download the file if we're in append modes
                        if "a" in mode or "+" in mode:
                            try:
                                resp = self._api_download_file_git(path)
                            except RetryError:
                                raise RuntimeError(f"Couldn't download {path.relative_path} after multiple attempts")
                            if resp.status_code < 400:
                                with self.__open(path.absolute_path, "wb") as output:
                                    output.write(resp.content)
                        return self.__open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)

        else:
            return self.__open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    def os_open(self, path, flags, mode=0o777, *, dir_fd=None):
        """
        os.open is supposed to be lower level, but it's still being used by e.g. Pathlib
        We're trying to wrap around it here, by parsing flags and calling the higher-level open
        Caveats: list of flags being handled is not exhaustive + mode doesn't work
                 (because we lose them when passing to builtin open)
        WARNING: DO NOT patch actual os.open with it, because the builtin uses os.open.
                 This is only for the purposes of patching pathlib.open in Python 3.9 and below.
                 Since Python 3.10 pathlib uses io.open, and in Python 3.11 they removed the accessor completely

        :meta private:
        """
        if dir_fd is not None:  # If dir_fd supplied, path is relative to that dir's fd, will handle in the future
            logger.debug("fs.os_open - NotImplemented")
            raise NotImplementedError("DagsHub's patched os.open() (for pathlib only) does not support dir_fd")
        path = self._parse_path(path)
        if path.is_in_repo:
            try:
                open_mode = "r"
                # Write modes - calling in append mode,
                # This way we create the intermediate folders if file doesn't exist, but the folder it's in does
                # Append so we don't truncate the file
                if not (flags & os.O_RDONLY):
                    open_mode = "a"
                logger.debug("fs.os_open - trying to materialize path")
                self.open(path.absolute_path, mode=open_mode).close()
                logger.debug("fs.os_open - successfully materialized path")
            except FileNotFoundError:
                logger.debug("fs.os_open - failed to materialize path, os.open will throw")
        return os.open(path.absolute_path, flags, mode, dir_fd=dir_fd)

    def stat(self, path, *args, dir_fd=None, follow_symlinks=True):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/os.html#os.stat)

        Get the status of a file or directory, including support for special files and DagsHub integration.

        Args:
            path (Union[str, int, bytes]): The path of the file or directory to get the status for.
                It can be a path (str), file descriptor (int), or bytes-like object.
            dir_fd (int, optional): File descriptor of the directory. Defaults to None.
            follow_symlinks (bool, optional): Whether to follow symbolic links. Defaults to True.

        Returns:
            collections.namedtuple: A namedtuple containing the file status information.

        :meta private:
        """
        # FD passthrough
        if type(path) is int:
            return self.__stat(path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

        if type(path) is bytes:
            path = os.fsdecode(path)
        if dir_fd is not None or not follow_symlinks:
            logger.debug("fs.stat - NotImplemented")
            raise NotImplementedError("DagsHub's patched stat() does not support dir_fd or follow_symlinks")
        parsed_path = self._parse_path(path)
        # todo: remove False
        if parsed_path.is_in_repo:
            logger.debug("fs.stat - is relative path")
            if parsed_path.is_passthrough_path:
                return self.__stat(parsed_path.absolute_path)
            elif parsed_path.relative_path == SPECIAL_FILE:
                return dagshub_stat_result(self, path, is_directory=False, custom_size=len(self._special_file()))
            else:
                try:
                    logger.debug(f"fs.stat - calling __stat - relative_path: {path}")
                    return self.__stat(parsed_path.absolute_path)
                except FileNotFoundError as err:
                    logger.debug("fs.stat - FileNotFoundError")
                    logger.debug(f"remote_tree: {self.remote_tree}")
                    parent_path = parsed_path.relative_path.parent
                    if str(parent_path) not in self.remote_tree:
                        try:
                            # Run listdir to update cache
                            self.listdir(self.project_root / parent_path)
                        except FileNotFoundError:
                            raise err

                    cached_remote_parent_tree = self.remote_tree.get(str(parent_path))
                    logger.debug(f"cached_remote_parent_tree: {cached_remote_parent_tree}")

                    if cached_remote_parent_tree is None:
                        raise err

                    filetype = cached_remote_parent_tree.get(parsed_path.name)
                    if filetype is None:
                        raise err

                    if filetype == "file":
                        return dagshub_stat_result(self, path, is_directory=False)
                    elif filetype == "dir":
                        self._mkdirs(parsed_path.absolute_path)
                        return self.__stat(parsed_path.absolute_path)
                    else:
                        raise RuntimeError(f"Unknown file type {filetype} for path {str(parsed_path)}")

        else:
            return self.__stat(path, follow_symlinks=follow_symlinks)

    def chdir(self, path):
        """
         NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/os.html#os.chdir)

        Change the current working directory to the specified path, with support for DagsHub integration.

        Args:
            path (Union[str, int, bytes]): The path to change the current working directory to.
                It can be a path (str), file descriptor (int), or bytes-like object.

        :meta private:
        """
        # FD check
        if type(path) is int:
            return self.__chdir(path)

        if type(path) is bytes:
            path = os.fsdecode(path)
        parsed_path = self._parse_path(path)
        if parsed_path.is_in_repo:
            try:
                self.__chdir(parsed_path.absolute_path)
            except FileNotFoundError:
                resp = self._api_listdir(parsed_path)
                # FIXME: if path is file, return FileNotFound instead of the listdir error
                if resp is not None:
                    self._mkdirs(parsed_path.absolute_path)
                    self.__chdir(parsed_path.absolute_path)
                else:
                    raise
        else:
            self.__chdir(path)

    def listdir(self, path="."):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/os.html#os.listdir)

        List the contents of a directory, including support for DagsHub integration.

        Args:
            path (str, optional): The path of the directory to list. Defaults to '.'.

        Raises:
            error: If an error occurs during the operation, it will be raised.

        Returns: A list of directory contents. If 'path' is a bytes object, the results will also be in bytes.

        :meta private:
        """
        # FD check
        if type(path) is int:
            return self.__listdir(path)

        # listdir needs to return results for bytes path arg also in bytes
        is_bytes_path_arg = type(path) is bytes

        def encode_results(res):
            res = list(res)
            if is_bytes_path_arg:
                res = [os.fsencode(p) for p in res]
            return res

        if is_bytes_path_arg:
            str_path = os.fsdecode(path)
        else:
            str_path = path
        parsed_path = self._parse_path(str_path)
        if parsed_path.is_in_repo:
            if parsed_path.is_passthrough_path:
                return self.listdir(parsed_path.original_path)
            else:
                dircontents: Set[str] = set()
                error = None
                try:
                    dircontents.update(self.__listdir(parsed_path.original_path))
                except FileNotFoundError as e:
                    error = e
                dircontents.update(
                    special.name
                    for special in self._get_special_paths(
                        parsed_path, self.project_root_dagshub_path, is_bytes_path_arg
                    )
                )
                # If we're accessing .dagshub/storage/s3/ we don't need to access the API, return straight away
                len_parts = len(parsed_path.relative_path.parts)
                if 0 < len_parts <= 3 and parsed_path.relative_path.parts[0] == ".dagshub":
                    return encode_results(dircontents)
                resp = self._api_listdir(parsed_path)
                if resp is not None:
                    dircontents.update(Path(f.path).name for f in resp)
                    self.remote_tree[str(parsed_path.relative_path)] = {Path(f.path).name: f.type for f in resp}
                    return encode_results(dircontents)
                else:
                    if error is not None:
                        raise error
                    else:
                        return encode_results(dircontents)

        else:
            return self.__listdir(path)

    @cached_property
    def project_root_dagshub_path(self):
        return DagshubPath(absolute_path=self.project_root, relative_path=Path(), original_path=Path(), fs=self)

    @wrapreturn(dagshub_ScandirIterator)
    def scandir(self, path="."):
        # FD check
        if type(path) is int:
            for direntry in self.__scandir(path):
                yield direntry
            return
        # scandir needs to return name and path as bytes, if entry arg is bytes
        is_bytes_path_arg = type(path) is bytes
        if is_bytes_path_arg:
            str_path = os.fsdecode(path)
        else:
            str_path = path
        parsed_path = self._parse_path(str_path)
        if parsed_path.is_in_repo and not parsed_path.is_passthrough_path:
            path = Path(str_path)
            local_filenames = set()
            try:
                for direntry in self.__scandir(path):
                    local_filenames.add(direntry.name)
                    yield direntry
            except FileNotFoundError:
                pass
            for special_entry in self._get_special_paths(
                parsed_path, self.project_root_dagshub_path / path, is_bytes_path_arg
            ):
                if special_entry.path not in local_filenames:
                    yield special_entry
            # Mix in the results from the API
            resp = self._api_listdir(parsed_path)
            if resp is not None:
                for f in resp:
                    name = PurePosixPath(f.path).name
                    if name not in local_filenames:
                        yield dagshub_DirEntry(self, parsed_path / name, f.type == "dir", is_binary=is_bytes_path_arg)
        else:
            for entry in self.__scandir(path):
                yield entry

    def _get_special_paths(
        self, dh_path: DagshubPath, relative_to: DagshubPath, is_binary: bool
    ) -> Set["dagshub_DirEntry"]:
        def generate_entry(path, is_directory):
            if isinstance(path, str):
                path = Path(path)
            return dagshub_DirEntry(self, relative_to / path, is_directory=is_directory, is_binary=is_binary)

        has_storages = len(self._storages) > 0
        res = set()
        str_path = dh_path.relative_path.as_posix()
        if str_path == ".":
            res.add(generate_entry(SPECIAL_FILE, False))
            if has_storages:
                res.add(generate_entry(".dagshub", True))
        elif str_path.startswith(".dagshub") and has_storages:
            storage_paths = [s.path_in_mount for s in self._storages]
            for sp in storage_paths:
                try:
                    relpath = sp.relative_to(dh_path.relative_path)
                    if relpath != Path():
                        res.add(generate_entry(relpath.parts[0], True))
                except ValueError:
                    continue
        return res

    def _api_listdir(self, path: DagshubPath, include_size: bool = False) -> Optional[List[ContentAPIEntry]]:
        response, hit = self._check_listdir_cache(path.relative_path.as_posix(), include_size)
        if hit:
            return response
        params: Dict[str, Any] = {"include_size": "true"} if include_size else {}
        if path.is_storage_path:
            params["paging"] = True
        url = self._content_url_for_path(path)

        def _get() -> Optional[Response]:
            resp = self.http_get(url, params=params, headers=config.requests_headers)
            if resp.status_code == 404:
                logger.debug(f"Got HTTP code {resp.status_code} while listing {path}, no results will be returned")
                return None
            elif resp.status_code >= 400:
                logger.warning(f"Got HTTP code {resp.status_code} while listing {path}, no results will be returned")
                return None
            return resp

        response = _get()
        if response is None:
            return None
        res: List[ContentAPIEntry] = []
        # Storage - token pagination, different return structure + if there's a token we do another request
        if path.is_storage_path:
            result = dacite.from_dict(StorageContentAPIResult, response.json())
            res += result.entries
            while result.next_token is not None:
                params["from_token"] = result.next_token
                new_resp = _get()
                if new_resp is None:
                    return None
                result = dacite.from_dict(StorageContentAPIResult, new_resp.json())
                res += result.entries
        else:
            for entry_raw in response.json():
                entry = dacite.from_dict(ContentAPIEntry, entry_raw)
                # Ignore storage root entries, we handle them separately in a different place
                if entry.type == "storage":
                    continue
                res.append(entry)

        self._listdir_cache[path.relative_path.as_posix()] = (res, include_size)
        return res

    def _check_listdir_cache(self, path: str, include_size: bool) -> Tuple[Optional[List[ContentAPIEntry]], bool]:
        # Checks that path has a pre-cached response
        # If include_size is True, but only a response without size is cached, that's a cache miss
        if path in self._listdir_cache:
            cache_val, with_size = self._listdir_cache[path]
            if not include_size or (include_size and with_size):
                return cache_val, True
        return None, False

    def _content_url_for_path(self, path: DagshubPath):
        if not path.is_in_repo:
            raise RuntimeError(f"Can't access path {path.absolute_path} outside of repo")
        str_path = path.relative_path.as_posix()
        if path.is_storage_path:
            path_to_access = str_path[len(".dagshub/storage/") :]
            return self._api.storage_content_api_url(path_to_access)
        return self._api.content_api_url(str_path, self._current_revision)

    def _raw_url_for_path(self, path: DagshubPath):
        if not path.is_in_repo:
            raise RuntimeError(f"Can't access path {path.absolute_path} outside of repo")
        str_path = path.relative_path.as_posix()
        if path.is_storage_path:
            path_to_access = str_path[len(".dagshub/storage/") :]
            return self._api.storage_raw_api_url(path_to_access)
        return self._api.raw_api_url(str_path, self._current_revision)

    @retry(
        retry=retry_if_result(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _api_download_file_git(self, path: DagshubPath):
        resp = self.http_get(self._raw_url_for_path(path), headers=config.requests_headers, timeout=None)
        return resp

    def http_get(self, path: str, **kwargs):
        timeout = self.timeout
        if "timeout" in kwargs:
            timeout = kwargs["timeout"]
            del kwargs["timeout"]
        return http_request("GET", path, auth=self.auth, timeout=timeout, **kwargs)

    def install_hooks(self):
        """
        Install hooks to override default file and directory operations with DagsHub-aware functionality.

        This method patches the standard Python I/O operations such as ``open``,
        ``stat``, ``listdir``, ``scandir``, and ``chdir`` with DagsHub-aware equivalents.
        Works inside a notebook and with Pathlib.

        If ``install_hooks()`` have already been called before, this method does nothing.

        Example::

            dagshub_fs = DagsHubFilesystem()
            dagshub_fs.install_hooks()

            with open("src/file_in_repo.txt") as f:
                print(f.read())

        Call :func:`~DagsHubFilesystem.uninstall_hooks` to undo the monkey patching.
        """
        if not hasattr(self.__class__, f"_{self.__class__.__name__}__unpatched"):
            # TODO: DRY this dictionary. i.e. __open() links cls.__open
            #  and io.open even though this dictionary links them
            #  Cannot use a dict as the source of truth because type hints rely on
            #  __get_unpatched inferring the right type
            self.__class__.__unpatched = {
                "open": builtins.open,
                "stat": os.stat,
                "listdir": os.listdir,
                "scandir": os.scandir,
                "chdir": os.chdir,
            }
            if PRE_PYTHON3_11:
                self.__class__.__unpatched["pathlib_open"] = _pathlib.open

        # IPython patches io.open to its own override, so we need to overwrite that also
        # More at _modified_open function in IPython sources:
        # https://github.com/ipython/ipython/blob/main/IPython/core/interactiveshell.py
        if is_inside_notebook() and not is_inside_colab():
            import IPython.core.interactiveshell

            instance = IPython.core.interactiveshell.InteractiveShell._instance  # noqa
            if instance is not None and hasattr(instance, "user_ns") and "open" in instance.user_ns:
                self.__class__.__unpatched["notebook_open"] = instance.user_ns["open"]
                instance.user_ns["open"] = self.open

        io.open = builtins.open = self.open
        os.stat = self.stat
        os.listdir = self.listdir
        os.scandir = self.scandir
        os.chdir = self.chdir
        if PRE_PYTHON3_11:
            if sys.version_info.minor == 10:
                # Python 3.10 - pathlib uses io.open
                _pathlib.open = self.open
            else:
                # Python <=3.9 - pathlib uses os.open
                _pathlib.open = self.os_open
            _pathlib.stat = self.stat
            _pathlib.listdir = self.listdir
            _pathlib.scandir = self.scandir

        self._install_framework_hooks()

        DagsHubFilesystem.hooked_instance = self

        msg = (
            f'Repository "{self._api.full_name}" is now hooked at path "{self.project_root}".\n'
            f"Any calls to Python file access function like open() and listdir() inside "
            f"of this directory will include results from the repository."
        )
        log_message(msg, logger)

    _framework_key_prefix = "framework_"

    def _install_framework_hooks(self):
        """
        Installs custom hook functions for frameworks
        """
        if self.frameworks is None:
            return
        for framework in self.frameworks:
            if framework not in self._framework_override_map:
                logger.warning(f"Framework {framework} not available for override, skipping")
                continue
            funcs = self._framework_override_map[framework]
            for func in funcs:
                module_name, func_name = func.rsplit(".", 1)
                class_name = None
                patch_class = None

                # Handle static class methods - we'll need to get the class from the module first
                if "$" in module_name:
                    module_name, class_name = module_name.split("$")
                    # Get rid of the . in the module name
                    module_name = module_name[:-1]

                try:
                    patch_module = importlib.import_module(module_name)
                    if class_name is not None:
                        patch_class = getattr(patch_module, class_name)
                        orig_fn = getattr(patch_class, func_name)
                    else:
                        orig_fn = getattr(patch_module, func_name)
                except ModuleNotFoundError:
                    logger.warning(f"Module [{module_name}] not found, so function [{func}] isn't being patched")
                    continue
                except AttributeError:
                    logger.warning(f"Function [{func}] not found, not patching it")
                    continue
                self.__class__.__unpatched[f"{self._framework_key_prefix}{func}"] = orig_fn
                if patch_class is not None:
                    setattr(patch_class, func_name, self._passthrough_decorator(orig_fn))
                else:
                    setattr(patch_module, func_name, self._passthrough_decorator(orig_fn))

    def _passthrough_decorator(self, orig_func, filearg: Union[int, str] = 0) -> Callable:
        """
        Decorator function over some other random function that assumes a file exists locally,
        but isn't using python's open(). These might be C++/Rust functions that use their respective opens.
        Examples: opencv, anything using pyo3

        Working around the problem by first calling open().close() to get the file.

        :param orig_func: the original function that needs to be called
        :param filearg: int or string, which arg/kwarg to use to get the filename
        :return: Wrapped orig_func
        """

        def passed_through(*args, **kwargs):
            if type(filearg) is str:
                filename = kwargs[filearg]
            else:
                filename = args[filearg]
            self.open(filename).close()
            return orig_func(*args, **kwargs)

        return passed_through

    @classmethod
    def uninstall_hooks(cls):
        """
        Reverses the changes made by :func:`install_hooks`, bringing back the builtin file I/O functions.
        """
        if hasattr(cls, f"_{cls.__name__}__unpatched"):
            io.open = builtins.open = cls.__unpatched["open"]
            os.stat = cls.__unpatched["stat"]
            os.listdir = cls.__unpatched["listdir"]
            os.scandir = cls.__unpatched["scandir"]
            os.chdir = cls.__unpatched["chdir"]
            if PRE_PYTHON3_11:
                _pathlib.open = cls.__unpatched["pathlib_open"]
                _pathlib.stat = cls.__unpatched["stat"]
                _pathlib.listdir = cls.__unpatched["listdir"]
                _pathlib.scandir = cls.__unpatched["scandir"]

            if "notebook_open" in cls.__unpatched:
                import IPython.core.interactiveshell

                instance = IPython.core.interactiveshell.InteractiveShell._instance  # noqa
                if instance is not None and hasattr(instance, "user_ns"):
                    instance.user_ns["open"] = cls.__unpatched["notebook_open"]

            cls._uninstall_framework_hooks()

        if DagsHubFilesystem.hooked_instance is not None:
            DagsHubFilesystem.hooked_instance.cleanup()
            DagsHubFilesystem.hooked_instance = None

    @classmethod
    def _uninstall_framework_hooks(cls):
        for func in list(filter(lambda key: key.startswith(cls._framework_key_prefix), cls.__unpatched.keys())):
            orig_fn = cls.__unpatched[func]
            orig_func_name = func

            func = func[len(cls._framework_key_prefix) :]
            module_name, func_name = func.rsplit(".", 1)
            class_name = None

            if "$" in module_name:
                module_name, class_name = module_name.split("$")
                # Get rid of the . in the module name
                module_name = module_name[:-1]

            m = importlib.import_module(module_name)
            if class_name is not None:
                patch_class = getattr(m, class_name)
                setattr(patch_class, func_name, orig_fn)
            else:
                setattr(m, func_name, orig_fn)

            del cls.__unpatched[orig_func_name]

    def _mkdirs(self, absolute_path: Path):
        for parent in list(absolute_path.parents)[::-1]:
            try:
                self.__stat(parent)
            except (OSError, ValueError):
                os.mkdir(parent)
        try:
            self.__stat(absolute_path)
        except (OSError, ValueError):
            os.mkdir(absolute_path)

    @classmethod
    def __get_unpatched(cls, key, alt: T) -> T:
        if hasattr(cls, f"_{cls.__name__}__unpatched"):
            return cls.__unpatched[key]
        else:
            return alt

    @property
    def __open(self):
        return self.__get_unpatched("open", builtins.open)

    @property
    def __stat(self):
        return self.__get_unpatched("stat", os.stat)

    @property
    def __listdir(self):
        return self.__get_unpatched("listdir", os.listdir)

    @property
    def __scandir(self):
        return self.__get_unpatched("scandir", os.scandir)

    @property
    def __chdir(self):
        return self.__get_unpatched("chdir", os.chdir)


def install_hooks(
    project_root: Optional[PathLike] = None,
    repo_url: Optional[str] = None,
    branch: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
    timeout: Optional[int] = None,
    exclude_globs: Optional[Union[List[str], str]] = None,
    frameworks: Optional[List[str]] = None,
):
    """
    Monkey patches builtin Python functions to make them DagsHub-repo aware.
    Patched functions are: ``open()``, ``os.listdir()``, ``os.scandir()``, ``os.stat()`` and \
    pathlib's functions that use them

    Calling this function is equivalent to creating a :class:`DagsHubFilesystem` object
    and calling its :func:`install_hooks() <dagshub.streaming.DagsHubFilesystem.install_hooks>` method

    For argument documentation, read :class:`.DagsHubFilesystem`

    Call :func:`uninstall_hooks` to undo the monkey patching.
    """
    fs = DagsHubFilesystem(
        project_root=project_root,
        repo_url=repo_url,
        branch=branch,
        username=username,
        password=password,
        token=token,
        timeout=timeout,
        exclude_globs=exclude_globs,
        frameworks=frameworks,
    )
    fs.install_hooks()


def uninstall_hooks():
    """
    Reverses the changes made by :func:`install_hooks`
    """
    DagsHubFilesystem.uninstall_hooks()


class dagshub_stat_result:
    def __init__(self, fs: "DagsHubFilesystem", path: DagshubPath, is_directory: bool, custom_size: int = None):
        self._fs = fs
        self._path = path
        self._is_directory = is_directory
        self._custom_size = custom_size
        assert not self._is_directory  # TODO make folder stats lazy?

    def __getattr__(self, name: str):
        if not name.startswith("st_"):
            raise AttributeError
        if hasattr(self, "_true_stat"):
            return os.stat_result.__getattribute__(self._true_stat, name)
        if name == "st_uid":
            return os.getuid()
        elif name == "st_gid":
            return os.getgid()
        elif name == "st_atime" or name == "st_mtime" or name == "st_ctime":
            return 0
        elif name == "st_mode":
            return 0o100644
        elif name == "st_size":
            if self._custom_size:
                return self._custom_size
            return 1100  # hardcoded size because size requests take a disproportionate amount of time
        self._fs.open(self._path)
        self._true_stat = self._fs._DagsHubFilesystem__stat(self._path.absolute_path)
        return os.stat_result.__getattribute__(self._true_stat, name)

    def __repr__(self):
        inner = repr(self._true_stat) if hasattr(self, "_true_stat") else "pending..."
        return f"dagshub_stat_result({inner}, path={self._path})"


class dagshub_DirEntry:
    def __init__(self, fs: "DagsHubFilesystem", path: DagshubPath, is_directory: bool = False, is_binary: bool = False):
        self._fs = fs
        self._path = path
        self._is_directory = is_directory
        self._is_binary = is_binary

    @property
    def name(self):
        # TODO: create decorator for delegation
        if hasattr(self, "_true_direntry"):
            name = self._true_direntry.name
        else:
            name = self._path.name
        return os.fsencode(name) if self._is_binary else name

    @property
    def path(self):
        if hasattr(self, "_true_direntry"):
            path = self._true_direntry.path
        else:
            path = str(self._path.original_path)
        return os.fsencode(path) if self._is_binary else path

    def is_dir(self):
        if hasattr(self, "_true_direntry"):
            return self._true_direntry.is_dir()
        else:
            return self._is_directory

    def is_file(self):
        if hasattr(self, "_true_direntry"):
            return self._true_direntry.is_file()
        else:
            # TODO: Symlinks should return false
            return not self._is_directory

    def stat(self):
        if hasattr(self, "_true_direntry"):
            return self._true_direntry.stat()
        else:
            return self._fs.stat(self._path.original_path)

    def __getattr__(self, name: str):
        if name == "_true_direntry":
            raise AttributeError
        if hasattr(self, "_true_direntry"):
            return os.DirEntry.__getattribute__(self._true_direntry, name)

        # Either create a dir, or download the file
        if self._is_directory:
            self._fs._mkdirs(self._path.absolute_path)
        else:
            self._fs.open(self._path.absolute_path)

        for direntry in self._fs._DagsHubFilesystem__scandir(self._path.original_path):
            if direntry.name == self._path.name:
                self._true_direntry = direntry
                return os.DirEntry.__getattribute__(self._true_direntry, name)
        else:
            raise FileNotFoundError

    def __repr__(self):
        cached = " (cached)" if hasattr(self, "_true_direntry") else ""
        return f"<dagshub_DirEntry '{self.name}'{cached}>"


# Used for testing purposes only
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    fs = DagsHubFilesystem()
    fs.install_hooks()

__all__ = [DagsHubFilesystem.__name__, install_hooks.__name__]
