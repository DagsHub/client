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
    """

    def __init__(self, fs: "DagsHubFilesystem", file_path: Union[str, bytes, PathLike, "DagshubPath"]):
        self.fs = fs
        self.absolute_path, self.relative_path, self.original_path = self.parse_path(file_path)

    def parse_path(self, file_path: Union[str, bytes, PathLike, "DagshubPath"]) -> Tuple[Path, Optional[Path], Path]:
        print(self.fs.project_root)
        if isinstance(file_path, DagshubPath):
            if file_path.fs != self.fs:
                relativized = DagshubPath(self.fs, file_path.absolute_path)
                return relativized.absolute_path, relativized.relative_path, relativized.original_path
            return file_path.absolute_path, file_path.relative_path, file_path.original_path
        if isinstance(file_path, bytes):
            file_path = os.fsdecode(file_path)
        orig_path = Path(file_path)
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
        return DagshubPath(
            self.fs,
            self.original_path / other,
        )
