import errno
import logging
import os
import platform
import sys
from argparse import ArgumentParser
from os import PathLike
from pathlib import Path
from threading import Lock
from typing import Optional
from dagshub.common import rich_console

from .filesystem import SPECIAL_FILE, DagsHubFilesystem

logger = logging.getLogger(__name__)

SPECIAL_FILE_FH = (1 << 64) - 1

fuse_enabled_systems = ["Linux"]
system = platform.system()
if system not in fuse_enabled_systems:
    err_str = (
        f"FUSE mounting isn't supported on {system}.\n"
        f"Please use install_hooks to access DagsHub hosted files from a python script"
    )
    raise ImportError(err_str)
from fuse import FUSE, FuseOSError, LoggingMixIn, Operations  # noqa


class DagsHubFUSE(LoggingMixIn, Operations):
    def __init__(
        self,
        project_root: Optional[PathLike] = None,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ):
        # FIXME TODO move autoconfiguration out of FUSE object constructor and to main method
        self.fs = DagsHubFilesystem(
            project_root=project_root,
            repo_url=repo_url,
            branch=branch,
            username=username,
            password=password,
            token=token,
        )
        logger.debug("__init__")
        self.rwlock = Lock()

    def __call__(self, op, path, *args):
        return super(DagsHubFUSE, self).__call__(op, self.fs.project_root / path[1:], *args)

    def access(self, path, mode):
        """
        Check file accessibility based on the given path and access mode.

        Args:
            path (Union[str, int, bytes]): The path to check accessibility.
                It can be a path (str), file descriptor (int), or bytes-like object.
            mode (int):
                The access mode to check.

        Returns:
            bool: True if the file is accessible; otherwise, False.

        Notes:
            - If the provided 'path' argument is an integer (file descriptor),
                the function behaves as a passthrough to the standard access() method.
            - The 'mode' argument follows the same convention as the os.access() function,
                where values like os.R_OK, os.W_OK, and os.X_OK indicate read, write, and execute permissions.

        Examples:
            ```python
            dh = DagsHubClient()
            is_accessible = dh.access('file.txt', os.R_OK)
            print(is_accessible)  # True if the file is readable, otherwise False
            ```
        """
        logger.debug(f"access - path: {path}, mode:{mode}")
        try:
            self.fs.stat(path)
        except FileNotFoundError:
            return False

    def open(self, path, flags):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/functions.html#open)

        Open a file for reading or writing.

        Args:
            path (Union[str, int, bytes]): The path of the file to open.
                It can be a path (str), file descriptor (int), or bytes-like object.
            flags (int): The flags for opening the file.

        Raises:
            FuseOSError: If an error occurs while opening the file, a FuseOSError is raised.

        Returns:
            int: The file descriptor for the opened file.

        """
        logger.debug(f"open - path: {path}, flags: {flags}")
        if path == Path(self.fs.project_root / SPECIAL_FILE):
            return SPECIAL_FILE_FH
        try:
            self.fs.open(path).close()
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)
        logger.debug("finished fs.open")
        return os.open(self.fs._relative_path(path), flags, dir_fd=self.fs.project_root_fd)

    def getattr(self, path, fd=None):
        """
        NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/functions.html#getattr)

        Get the attributes of a file or directory.

        Args:
            path (Union[str, int, bytes]): The path to the file or directory.
                It can be a path (str), file descriptor (int), or bytes-like object.
            fd (int, optional): An optional file descriptor. Defaults to None.

        Raises:
            FuseOSError: If the file or directory does not exist, a FuseOSError is raised.

        """
        logger.debug(f"getattr - path:{str(path)}, fd:{fd}")
        try:
            if fd:
                logger.debug("with __stat")
                st = self.fs._DagsHubFilesystem__stat(fd)
            else:
                logger.debug("with fs.stat")
                st = self.fs.stat(path)

            logger.debug(f"st: {st}")
            return {
                key: getattr(st, key)
                for key in (
                    "st_atime",
                    "st_ctime",
                    "st_gid",
                    "st_mode",
                    "st_mtime",
                    # 'st_nlink',
                    "st_size",
                    "st_uid",
                )
            }
        except FileNotFoundError:
            logger.debug("FileNotFound")
            raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        """
         NOTE: This is a wrapper function for python's built-in file operations
            (https://docs.python.org/3/library/os.html#os.read)

        Read data in the form of bytes from a file.

        Args:
            path (Union[str, int, bytes]): The path of the file to read. It can be a path (str),
                file descriptor (int), or bytes-like object.
            size (int): The size of data to read.
            offset (int): The offset in the file.
            fh (int): The file descriptor.

        """
        logger.debug(f"read - path: {path}, offset: {offset}, fh: {fh}")
        if fh == SPECIAL_FILE_FH:
            return self.fs._special_file()[offset : offset + size]
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        """
        List the contents of a directory.

        Args:
            path (Union[str, int, bytes]): The path of the directory.
                It can be a path (str), file descriptor (int), or bytes-like object.
            fh (int): The file descriptor.

        Returns:
            List[str]: A list of directory contents.

        """
        logger.debug(f"readdir - path: {path}, fh: {fh}")
        return [".", ".."] + self.fs.listdir(path)

    def release(self, path, fh):
        """
        Release the resources associated with an open file.

        Args:
            path (Union[str, int, bytes]):
                The path of the file.
                It can be a path (str), file descriptor (int), or bytes-like object.
            fh (int):
                The file descriptor.

        Notes:
            - If the provided 'path' argument is an integer (file descriptor),
                the function behaves as a passthrough to the standard os.close() method.
            - Special file descriptors, such as SPECIAL_FILE_FH, are not closed.

        Examples:
            ```python
            dh = DagsHubClient()
            dh.release('file.txt', file_descriptor)
            ```
        """
        logger.debug(f"release - path: {path}, fh: {fh}")
        if fh != SPECIAL_FILE_FH:
            return os.close(fh)


def mount(
    debug=False,
    project_root: Optional[PathLike] = None,
    repo_url: Optional[str] = None,
    branch: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
):
    """
    Mount a DagsHubFUSE filesystem.

    Args:
        debug (bool, optional): If True, run the FUSE filesystem in the foreground with debug logging;
            otherwise, run it in the background. Defaults to False.
        project_root (Optional[PathLike], optional): The local directory to mount as the DagsHubFUSE filesystem.
            Defaults to None.
        repo_url (Optional[str], optional): The URL of the DagsHub repository to mount. Defaults to None.
        branch (Optional[str], optional): The branch of the DagsHub repository to mount. Defaults to None.
        username (Optional[str], optional): The username for authentication. Defaults to None.
        password (Optional[str], optional): The password for authentication. Defaults to None.
        token (Optional[str], optional): The token for authentication. Defaults to None.

    Notes:
        - If the 'debug' parameter is True, the filesystem is run in the foreground with debug logging.
        - If 'debug' is False, the filesystem runs in the background.

    Example:
        ```python
        mount(debug=True, project_root='/path/local/dir', repo_url='https://dagshub.com/user/repo.git', branch='main')
        ```
    """
    logging.basicConfig(level=logging.DEBUG)
    fuse = DagsHubFUSE(
        project_root=project_root, repo_url=repo_url, branch=branch, username=username, password=password, token=token
    )
    rich_console.print(
        f"Mounting DagsHubFUSE filesystem at {fuse.fs.project_root}\n"
        f"Run `cd .` in any existing terminals to utilize mounted FS."
    )
    FUSE(fuse, str(fuse.fs.project_root), foreground=debug, nonempty=True)
    if not debug:
        os.chdir(os.path.realpath(os.curdir))
    # TODO: Clean unmounting procedure


def main():
    parser = ArgumentParser()
    parser.add_argument("project_root", nargs="?")
    parser.add_argument("--repo_url")
    parser.add_argument("--branch")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--debug", action="store_true", default=False)  # default=False, nargs=0)

    args = parser.parse_args()

    if not args.debug:
        # Hide tracebacks of errors, display only error message
        sys.tracebacklimit = 0

    mount(**vars(args))


if __name__ == "__main__":
    main()
