import logging
import os
from errno import EACCES
from pathlib import Path
from threading import Lock

from fuse import FUSE, FuseOSError, LoggingMixIn, Operations

from filesystem import DagsHubFilesystem

class DagsHubFUSE(LoggingMixIn, Operations):
    def __init__(self, project_root):
        # FIXME TODO move autoconfiguration out of FUSE object constructor and to main method
        self.fs = DagsHubFilesystem(project_root=Path(project_root))
        self.rwlock = Lock()

    def __call__(self, op, path, *args):
        return super(DagsHubFUSE, self).__call__(op, self.fs.project_root / path[1:], *args)

    def access(self, path, mode):
        try:
            self.fs.stat(path)
        except FileNotFoundError:
            return False

    def open(self, path, flags):
        self.fs.open(path).close()
        return os.open(path, flags, dir_fd=self.fs.project_root_fd)

    def getattr(self, path, fd=None):
        try:
            if fd:
                st = self.fs._DagsHubFilesystem__stat(fd)
            else:
                st = self.fs.stat(path)
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
            raise FuseOSError(2)#errno.ENOENT

    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        return ['.', '..'] + self.fs.listdir(path)

    def release(self, path, fh):
        return os.close(fh)

def mount(foreground=False):
    # FIXME TODO Better configurability
    logging.basicConfig(level=logging.DEBUG)
    fuse = DagsHubFUSE(os.curdir)
    FUSE(fuse, str(fuse.fs.project_root), foreground=foreground, nonempty=True)
    if not foreground:
        os.chdir(os.path.realpath(os.curdir))

if __name__ == '__main__':
    mount(foreground=True)
