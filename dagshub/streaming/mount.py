import errno
import logging
import os
import sys
from argparse import ArgumentParser
from os import PathLike
from pathlib import Path
from threading import Lock
from typing import Optional

from fuse import FUSE, FuseOSError, LoggingMixIn, Operations

from .filesystem import SPECIAL_FILE, DagsHubFilesystem

SPECIAL_FILE_FH = (1<<64)-1

class DagsHubFUSE(LoggingMixIn, Operations):
    def __init__(self,
                 project_root: Optional[PathLike] = None,
                 repo_url: Optional[str] = None,
                 branch: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        # FIXME TODO move autoconfiguration out of FUSE object constructor and to main method
        self.fs = DagsHubFilesystem(project_root=project_root, repo_url=repo_url, branch=branch, username=username, password=password)
        self.rwlock = Lock()
        self.depth = 0

    def __call__(self, op, path, *args):
        return super(DagsHubFUSE, self).__call__(op, self.fs.project_root / path[1:], *args)

    def access(self, path, mode):
        try:
            self.fs.stat(path)
        except FileNotFoundError:
            return False

    def open(self, path, flags):
        if path == Path(self.fs.project_root / SPECIAL_FILE):
            return SPECIAL_FILE_FH
        self.fs.open(path).close()
        return os.open(path, flags, dir_fd=self.fs.project_root_fd)

    def getattr(self, path, fd=None):
        try:
            if fd:
                st = self.fs._DagsHubFilesystem__stat(fd)
            else:
                st = self.fs.stat(path)
            self.depth += 1
            return {
                key: getattr(st, key)
                for key in (
                    'st_atime',
                    'st_ctime',
                    'st_gid',
                    'st_mode',
                    'st_mtime',
                    # 'st_nlink',
                    'st_size',
                    'st_uid',
                )
            }
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        if fh == SPECIAL_FILE_FH:
            return self.fs._special_file()[offset:offset+size]
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        return ['.', '..'] + self.fs.listdir(path)

    def release(self, path, fh):
        if fh != SPECIAL_FILE_FH: 
            return os.close(fh)

def mount(debug=False,
          project_root: Optional[PathLike] = None,
          repo_url: Optional[str] = None,
          branch: Optional[str] = None,
          username: Optional[str] = None,
          password: Optional[str] = None):
    logging.basicConfig(level=logging.DEBUG)
    fuse = DagsHubFUSE(project_root=project_root, repo_url=repo_url, branch=branch, username=username, password=password)
    print(f'Mounting DagsHubFUSE filesystem at {fuse.fs.project_root}\nRun `cd .` in any existing terminals to utilize mounted FS.')
    FUSE(fuse, str(fuse.fs.project_root), foreground=debug, nonempty=True)
    if not debug:
        os.chdir(os.path.realpath(os.curdir))
    # TODO: Clean unmounting procedure

def main():
    parser = ArgumentParser()
    parser.add_argument('project_root', nargs='?')
    parser.add_argument('--repo_url')
    parser.add_argument('--branch')
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--debug', action='store_true', default=False)#  default=False, nargs=0)

    args = parser.parse_args()

    if not args.debug:
        # Hide tracebacks of errors, display only error message
        sys.tracebacklimit = 0

    mount(**vars(args))

if __name__ == '__main__':
	main()
