import os
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union, Tuple

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

if TYPE_CHECKING:
    from filesystem import DagsHubFilesystem

storage_schemas = ["s3", "gs", "azure"]


@dataclass
class DagshubPath:
    """
    Class for handling any path used inside the virtual filesystem

    Attributes:
        fs (DagsHubFilesystem): Filesystem from which this path is assigned
        absolute_path (Path): Absolute path in the system
        relative_path (Optional[Path]): Path relative to the root of the encapsulating FileSystem.
                                        If None, path is outside the FS
        original_path (Path): Original path as it was accessed by the user
        is_binary_path_requested (bool): For functions like scandir and listdir that have
            different behaviour whether user requested a string or a binary path
    """

    def __init__(self, fs: "DagsHubFilesystem", file_path: Union[str, bytes, PathLike, "DagshubPath"]):
        self.fs = fs
        self.is_binary_path_requested = isinstance(file_path, bytes)
        self.absolute_path, self.relative_path, self.original_path = self.parse_path(file_path)

    def parse_path(
        self, file_path: Union[str, bytes, PathLike, "DagshubPath"]
    ) -> Tuple[Path, Optional[Path], Union[str, bytes, PathLike]]:
        if isinstance(file_path, DagshubPath):
            self.is_binary_path_requested = file_path.is_binary_path_requested
            if file_path.fs != self.fs:
                relativized = DagshubPath(self.fs, file_path.absolute_path)
                return relativized.absolute_path, relativized.relative_path, relativized.original_path
            return file_path.absolute_path, file_path.relative_path, file_path.original_path
        orig_path = file_path
        if isinstance(file_path, bytes):
            file_path = os.fsdecode(file_path)
        abspath = Path(os.path.abspath(file_path))
        try:
            relpath = abspath.relative_to(os.path.abspath(self.fs.project_root))
            if str(relpath).startswith("<"):
                return abspath, None, orig_path
            return abspath, relpath, orig_path
        except ValueError:
            return abspath, None, orig_path

    def handle_storages(self):
        # Handle storage paths - translate s3:/bla-bla to .dagshub/storage/s3/bla-bla
        if self.relative_path is not None:
            str_path = self.relative_path.as_posix()
            for storage_schema in storage_schemas:
                if str_path.startswith(f"{storage_schema}:/"):
                    str_path = str_path[len(storage_schema) + 2 :]
                    self.relative_path = Path(".dagshub/storage") / storage_schema / str_path
                    self.absolute_path = self.fs.project_root / self.relative_path
                    break

    @cached_property
    def name(self):
        assert self.absolute_path is not None
        return self.absolute_path.name

    @cached_property
    def is_in_repo(self):
        return self.absolute_path is not None and self.relative_path is not None

    @cached_property
    def is_storage_path(self):
        """
        Is path a storage path (stored in a bucket)
        Those paths are accessible via a path like `.dagshub/storage/s3/bucket/...`
        """
        if self.relative_path is None:
            return False
        return self.relative_path.as_posix().startswith(".dagshub/storage")

    def is_passthrough_path(self, fs: "DagsHubFilesystem"):
        """
        Is path a "passthrough" path
        A passthrough path is a path that the FS ignores when trying to look up if the file exists on DagsHub
        This includes:
            - .git and .dvc folders - that prevents accidental access to their caches.
                If you need to read with streaming from a .dvc folder (to read config for example), please pull the repo
            - Any /site-packages/ folder - if you have a venv in your repo, python will try to find packages there.
        """
        if self.relative_path is None:
            return True
        str_path = self.relative_path.as_posix()
        if "/site-packages/" in str_path or str_path.endswith("/site-packages"):
            return True
        if str_path.startswith((".git/", ".dvc/")) or str_path in (".git", ".dvc"):
            return True
        return any((self.relative_path.match(glob) for glob in fs.exclude_globs))

    def __truediv__(self, other):
        new = DagshubPath(
            self.fs,
            Path(self.original_path) / other,
        )
        new.is_binary_path_requested = self.is_binary_path_requested
        return new


class DagshubScandirIterator:
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


class DagshubStatResult:
    def __init__(
        self, fs: "DagsHubFilesystem", path: DagshubPath, is_directory: bool, custom_size: Optional[int] = None
    ):
        self._fs = fs
        self._path = path
        self._is_directory = is_directory
        self._custom_size = custom_size
        self._true_stat: Optional[os.stat_result] = None
        assert not self._is_directory  # TODO make folder stats lazy?

    def __getattr__(self, name: str):
        if not name.startswith("st_"):
            raise AttributeError
        if self._true_stat is not None:
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
            if self._custom_size is not None:
                return self._custom_size
            return 1100  # hardcoded size because size requests take a disproportionate amount of time
        self._fs.open(self._path)
        self._true_stat = self._fs.original_stat(self._path.absolute_path)
        return os.stat_result.__getattribute__(self._true_stat, name)

    def __repr__(self):
        inner = repr(self._true_stat) if self._true_stat is not None else "pending..."
        return f"dagshub_stat_result({inner}, path={self._path})"


class DagshubDirEntry:
    def __init__(self, fs: "DagsHubFilesystem", path: DagshubPath, is_directory: bool = False, is_binary: bool = False):
        self._fs = fs
        self._path = path
        self._is_directory = is_directory
        self._is_binary = is_binary
        self._true_direntry: Optional[os.DirEntry] = None

    @property
    def name(self):
        if self._true_direntry is not None:
            name = self._true_direntry.name
        else:
            name = self._path.name
        return os.fsencode(name) if self._is_binary else name

    @property
    def path(self):
        if self._true_direntry is not None:
            path = self._true_direntry.path
        else:
            path = str(self._path.original_path)
        return os.fsencode(path) if self._is_binary else path

    def is_dir(self):
        if self._true_direntry is not None:
            return self._true_direntry.is_dir()
        else:
            return self._is_directory

    def is_file(self):
        if self._true_direntry is not None:
            return self._true_direntry.is_file()
        else:
            # TODO: Symlinks should return false
            return not self._is_directory

    def stat(self):
        if self._true_direntry is not None:
            return self._true_direntry.stat()
        else:
            return self._fs.stat(self._path.original_path)

    def __getattr__(self, name: str):
        if name == "_true_direntry":
            raise AttributeError
        if self._true_direntry is not None:
            return os.DirEntry.__getattribute__(self._true_direntry, name)

        # Either create a dir, or download the file
        if self._is_directory:
            self._fs.mkdirs(self._path.absolute_path)
        else:
            self._fs.open(self._path.absolute_path)

        for direntry in self._fs.original_stat(self._path.original_path):
            if direntry.name == self._path.name:
                self._true_direntry = direntry
                return os.DirEntry.__getattribute__(self._true_direntry, name)
        else:
            raise FileNotFoundError

    def __repr__(self):
        cached = " (cached)" if self._true_direntry is not None else ""
        return f"<dagshub_DirEntry '{self.name}'{cached}>"


PathType = Union[str, int, bytes, PathLike]
PathTypeWithDagshubPath = Union[PathType, DagshubPath]
