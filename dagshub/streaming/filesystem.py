import io
import logging
import os
import re
import subprocess
from configparser import ConfigParser
from multiprocessing import AuthenticationError
from os import PathLike
from pathlib import Path, PurePosixPath
from typing import Optional, TypeVar, Union, Dict, Set, Tuple, List
from urllib.parse import urlparse, ParseResult

from tenacity import RetryError

from dagshub.common import config
from dagshub.common.api.repo import RepoAPI, CommitNotFoundError, PathNotFoundError, DagsHubHTTPError
from dagshub.common.api.responses import ContentAPIEntry
from dagshub.common.helpers import get_project_root
from dagshub.streaming.dataclasses import (
    DagshubPath,
    DagshubScandirIterator,
    DagshubDirEntry,
    DagshubStatResult,
    PathTypeWithDagshubPath,
)
from dagshub.streaming.hook_router import HookRouter
from dagshub.streaming.util import wrapreturn

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

T = TypeVar("T")
logger = logging.getLogger(__name__)


SPECIAL_FILE = Path(".dagshub-streaming")


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
        self.project_root: Path
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

        self.exclude_globs: List[str]
        if exclude_globs is None:
            self.exclude_globs = []
        elif isinstance(exclude_globs, str):
            self.exclude_globs = [exclude_globs]
        else:
            self.exclude_globs = exclude_globs

        self._listdir_cache: Dict[str, Tuple[Optional[List[ContentAPIEntry]], bool]] = {}

        self.repo_api = self._generate_repo_api(self.parsed_repo_url)

        # Check that the repo is accessible by accessing the content root
        response = self._api_listdir(DagshubPath(self, self.project_root))
        if response is None:
            # TODO: Check .dvc/config{,.local} for credentials
            raise AuthenticationError("DagsHub credentials required, however none provided or discovered")

        self._storages = self.repo_api.get_connected_storages()

    def _generate_repo_api(self, repo_url: ParseResult) -> RepoAPI:
        host = f"{repo_url.scheme}://{repo_url.netloc}"
        repo = repo_url.path
        return RepoAPI(repo=repo, host=host, auth=self.auth)

    @cached_property
    def current_revision(self) -> str:
        """
        Gets current revision on repo:
        - If User specified a branch, returns HEAD of that brunch on the remote
        - If branch wasn't detected, returns HEAD of default branch in the specified remote.
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
                branch = self.repo_api.default_branch

        # check if it is a commit sha, in that case do not load the sha
        sha_regex = re.compile(r"^([a-f0-9]){5,40}$")
        if sha_regex.match(branch):
            try:
                self.repo_api.get_commit_info(branch)
                return branch
            except CommitNotFoundError:
                pass

        return self.repo_api.last_commit_sha(branch)

    def is_commit_on_remote(self, sha1):
        try:
            self.repo_api.get_commit_info(sha1)
            return True
        except CommitNotFoundError:
            return False

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
        proc = subprocess.run(
            ["git", "credential", "fill"], input=f"url={self.parsed_repo_url.geturl()}".encode(), capture_output=True
        )
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
            assert remote.hostname is not None
            remote = remote._replace(netloc=remote.hostname)
            remote = remote._replace(path=re.compile(r"(\.git)?/?$").sub("", remote.path))
            res_remotes.append(remote.geturl())
        return res_remotes

    @staticmethod
    def _special_file():
        # TODO Include more information in this file
        return b"v0\n"

    def open(
        self,
        file: PathTypeWithDagshubPath,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
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
        if isinstance(file, int):
            return self.original_open(file, mode, buffering, encoding, errors, newline, closefd)

        if isinstance(file, bytes):
            file = os.fsdecode(file)
        path = DagshubPath(self, file)
        if path.is_in_repo:
            assert path.relative_path is not None
            assert path.absolute_path is not None
            if opener is not None:
                raise NotImplementedError("DagsHub's patched open() does not support custom openers")
            if path.is_passthrough_path(self):
                return self.original_open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)
            elif path.relative_path == SPECIAL_FILE:
                return io.BytesIO(self._special_file())
            else:
                try:
                    return self.original_open(path.absolute_path, mode, buffering, encoding, errors, newline, closefd)
                except FileNotFoundError as err:
                    # Open for reading - try to download the file
                    if "r" in mode:
                        try:
                            contents = self._api_download_file_git(path)
                        except RetryError:
                            raise RuntimeError(f"Couldn't download {path.relative_path} after multiple attempts")
                        except PathNotFoundError:
                            raise FileNotFoundError(f"Error finding {path.relative_path} in repo or on DagsHub")
                        self.mkdirs(path.absolute_path.parent)
                        # TODO: Handle symlinks
                        with self.original_open(path.absolute_path, "wb") as output:
                            output.write(contents)
                        return self.original_open(
                            path.absolute_path, mode, buffering, encoding, errors, newline, closefd
                        )
                    # Write modes - make sure that the folder is a tracked folder (create if it doesn't exist on disk),
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
                                contents = self._api_download_file_git(path)
                            except RetryError:
                                raise RuntimeError(f"Couldn't download {path.relative_path} after multiple attempts")
                            except PathNotFoundError:
                                raise FileNotFoundError(f"Error finding {path.relative_path} in repo or on DagsHub")
                            with self.original_open(path.absolute_path, "wb") as output:
                                output.write(contents)
                        return self.original_open(
                            path.absolute_path, mode, buffering, encoding, errors, newline, closefd
                        )

        else:
            return self.original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    def os_open(self, path: Union[str, bytes, PathLike, DagshubPath], flags, mode=0o777, *, dir_fd=None):
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
        dh_path = DagshubPath(self, path)
        if dh_path.is_in_repo:
            assert dh_path.relative_path is not None
            try:
                open_mode = "r"
                # Write modes - calling in append mode,
                # This way we create the intermediate folders if file doesn't exist, but the folder it's in does
                # Append, so we don't truncate the file
                if not (flags & os.O_RDONLY):
                    open_mode = "a"
                logger.debug("fs.os_open - trying to materialize path")
                self.open(dh_path.absolute_path, mode=open_mode).close()
                logger.debug("fs.os_open - successfully materialized path")
            except FileNotFoundError:
                logger.debug("fs.os_open - failed to materialize path, os.open will throw")
        return os.open(dh_path.absolute_path, flags, mode, dir_fd=dir_fd)

    def stat(self, path: PathTypeWithDagshubPath, *args, dir_fd=None, follow_symlinks=True):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/os.html#os.stat)

        Get the status of a file or directory, including support for special files and DagsHub integration.

        Args:
            path: The path of the file or directory to get the status for.
                It can be a path (str), file descriptor (int), or bytes-like object.
            dir_fd (int, optional): File descriptor of the directory. Defaults to None.
            follow_symlinks (bool, optional): Whether to follow symbolic links. Defaults to True.

        Returns:
            collections.namedtuple: A namedtuple containing the file status information.

        :meta private:
        """
        # FD passthrough
        if isinstance(path, int):
            return self.original_stat(path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

        if isinstance(path, bytes):
            path = os.fsdecode(path)
        if dir_fd is not None or not follow_symlinks:
            logger.debug("fs.stat - NotImplemented")
            raise NotImplementedError("DagsHub's patched stat() does not support dir_fd or follow_symlinks")
        parsed_path = DagshubPath(self, path)
        if parsed_path.is_in_repo:
            assert parsed_path.relative_path is not None
            assert parsed_path.absolute_path is not None
            logger.debug("fs.stat - is relative path")
            if parsed_path.is_passthrough_path(self):
                return self.original_stat(parsed_path.absolute_path)
            elif parsed_path.relative_path == SPECIAL_FILE:
                return DagshubStatResult(self, parsed_path, is_directory=False, custom_size=len(self._special_file()))
            else:
                try:
                    logger.debug(f"fs.stat - calling __stat - relative_path: {path}")
                    return self.original_stat(parsed_path.absolute_path)
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
                        return DagshubStatResult(self, parsed_path, is_directory=False)
                    elif filetype == "dir":
                        self.mkdirs(parsed_path.absolute_path)
                        return self.original_stat(parsed_path.absolute_path)
                    else:
                        raise RuntimeError(f"Unknown file type {filetype} for path {str(parsed_path)}")
        else:
            return self.original_stat(path, follow_symlinks=follow_symlinks)

    def chdir(self, path: PathTypeWithDagshubPath):
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
        if isinstance(path, int):
            return self.original_chdir(path)

        if isinstance(path, bytes):
            path = os.fsdecode(path)
        parsed_path = DagshubPath(self, path)
        if parsed_path.is_in_repo:
            try:
                self.original_chdir(parsed_path.absolute_path)
            except FileNotFoundError:
                resp = self._api_listdir(parsed_path)
                # FIXME: if path is file, return FileNotFound instead of the listdir error
                if resp is not None:
                    self.mkdirs(parsed_path.absolute_path)
                    self.original_chdir(parsed_path.absolute_path)
                else:
                    raise
        else:
            self.original_chdir(path)

    def listdir(self, path: PathTypeWithDagshubPath = "."):
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
        if isinstance(path, int):
            return self.original_listdir(path)

        parsed_path = DagshubPath(self, path)

        # listdir needs to return results for bytes path arg also in bytes
        def encode_results(res):
            res = list(res)
            if parsed_path.is_binary_path_requested:
                res = [os.fsencode(p) for p in res]
            return res

        if parsed_path.is_in_repo:
            if parsed_path.is_passthrough_path(self):
                return self.listdir(parsed_path.original_path)
            else:
                dircontents: Set[str] = set()
                error = None
                try:
                    dircontents.update(self.original_listdir(parsed_path.original_path))
                except FileNotFoundError as e:
                    error = e
                dircontents.update(
                    special.name
                    for special in self._get_special_paths(
                        parsed_path, self.project_root_dagshub_path, parsed_path.is_binary_path_requested
                    )
                )
                # If we're accessing .dagshub/storage/s3/ we don't need to access the API, return straight away
                assert parsed_path.relative_path is not None
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
            return self.original_listdir(path)

    @cached_property
    def project_root_dagshub_path(self):
        return DagshubPath(self, self.project_root)

    @wrapreturn(DagshubScandirIterator)
    def scandir(self, path: PathTypeWithDagshubPath = "."):
        # FD check
        if isinstance(path, int):
            for direntry in self.original_scandir(path):
                yield direntry
            return

        parsed_path = DagshubPath(self, path)

        if parsed_path.is_in_repo and not parsed_path.is_passthrough_path(self):
            path = Path(parsed_path.original_path)
            local_filenames = set()
            try:
                for direntry in self.original_scandir(path):
                    local_filenames.add(direntry.name)
                    yield direntry
            except FileNotFoundError:
                pass
            for special_entry in self._get_special_paths(
                parsed_path, self.project_root_dagshub_path / path, parsed_path.is_binary_path_requested
            ):
                if special_entry.path not in local_filenames:
                    yield special_entry
            # Mix in the results from the API
            resp = self._api_listdir(parsed_path)
            if resp is not None:
                for f in resp:
                    name = PurePosixPath(f.path).name
                    if name not in local_filenames:
                        yield DagshubDirEntry(
                            self, parsed_path / name, f.type == "dir", is_binary=parsed_path.is_binary_path_requested
                        )
        else:
            for entry in self.original_scandir(path):
                yield entry

    def _get_special_paths(
        self, dh_path: DagshubPath, relative_to: DagshubPath, is_binary: bool
    ) -> Set["DagshubDirEntry"]:
        def generate_entry(path, is_directory):
            if isinstance(path, str):
                path = Path(path)
            return DagshubDirEntry(self, relative_to / path, is_directory=is_directory, is_binary=is_binary)

        has_storages = len(self._storages) > 0
        res = set()
        assert dh_path.relative_path is not None
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
        assert path.relative_path is not None

        repo_path = path.relative_path.as_posix()
        response, hit = self._check_listdir_cache(repo_path, include_size)
        if hit:
            return response

        res: List[ContentAPIEntry]
        try:
            if path.is_storage_path:
                storage_path = repo_path[len(".dagshub/storage/") :]
                res = self.repo_api.list_storage_path(storage_path, include_size=include_size)
            else:
                res = self.repo_api.list_path(repo_path, self.current_revision, include_size=include_size)
        except PathNotFoundError:
            self._listdir_cache[repo_path] = (None, True)
            return None
        except DagsHubHTTPError:
            return None

        self._listdir_cache[repo_path] = (res, include_size)
        return res

    def _check_listdir_cache(self, path: str, include_size: bool) -> Tuple[Optional[List[ContentAPIEntry]], bool]:
        # Checks that path has a pre-cached response
        # If include_size is True, but only a response without size is cached, that's a cache miss
        if path in self._listdir_cache:
            cache_val, with_size = self._listdir_cache[path]
            if not include_size or (include_size and with_size):
                return cache_val, True
        return None, False

    def _api_download_file_git(self, path: DagshubPath) -> bytes:
        if path.relative_path is None:
            raise RuntimeError(f"Can't access path {path.absolute_path} outside of repo")
        str_path = path.relative_path.as_posix()
        if path.is_storage_path:
            str_path = str_path[len(".dagshub/storage/") :]
            return self.repo_api.get_storage_file(str_path)
        return self.repo_api.get_file(str_path, self.current_revision)

    def mkdirs(self, absolute_path: Path):
        for parent in list(absolute_path.parents)[::-1]:
            try:
                self.original_stat(parent)
            except (OSError, ValueError):
                os.mkdir(parent)
        try:
            self.original_stat(absolute_path)
        except (OSError, ValueError):
            os.mkdir(absolute_path)

    def __del__(self):
        self.uninstall_hooks()

    @property
    def original_open(self):
        return HookRouter.original_open

    @property
    def original_stat(self):
        return HookRouter.original_stat

    @property
    def original_listdir(self):
        return HookRouter.original_listdir

    @property
    def original_scandir(self):
        return HookRouter.original_scandir

    @property
    def original_chdir(self):
        return HookRouter.original_chdir

    def install_hooks(self):
        HookRouter.hook_repo(self, frameworks=self.frameworks)

    def uninstall_hooks(self):
        HookRouter.unhook_repo(fs=self)


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
    HookRouter.hook_repo(fs, frameworks)


def uninstall_hooks(fs: Optional["DagsHubFilesystem"] = None, path: Optional[Union[str, PathLike]] = None):
    """
    Reverses the changes made by :func:`install_hooks`
    You can specify a filesystem or a path to unhook just one specific filesystem
    If nothing is specified, all current hooks will be cancelled

    Args:
        fs: DagsHubFilesystem
    """
    if fs is not None or path is not None:
        HookRouter.unhook_repo(fs=fs, path=path)
    else:
        # Uninstall everything
        HookRouter.uninstall_monkey_patch()


def get_mounted_filesystems() -> List[Tuple[Path, "DagsHubFilesystem"]]:
    """
    Returns all currently mounted filesystems
    Returns:
        List of tuples of (<full mount path>, <fs object>)
    """
    return [(fs.project_root, fs) for fs in HookRouter.active_filesystems]


__all__ = [
    DagsHubFilesystem.__name__,
    install_hooks.__name__,
    uninstall_hooks.__name__,
    get_mounted_filesystems.__name__,
]
