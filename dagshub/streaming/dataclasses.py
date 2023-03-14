from dataclasses import dataclass
from enum import auto, Flag
from pathlib import Path
from typing import Optional, Any

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

@dataclass
class StorageAPIEntry:
    name: str
    protocol: str
    list_path: str

    @property
    def full_path(self):
        return f"{self.protocol}/{self.name}"

    @property
    def path_in_mount(self) -> Path:
        return Path(".dagshub/storage") / self.protocol / self.name

@dataclass
class ContentAPIEntry:
    path: str
    # Possible values: dir, file, storage
    type: str
    size: int
    hash: str
    # Possible values: git, dvc, bucket
    versioning: str
    download_url: str
    content_url: Optional[str]  # TODO: remove Optional once content_url is exposed in API


class DagshubPathType(Flag):
    UNKNOWN = auto()
    TRACKED_IN_REPO = auto()
    OUT_OF_REPO = auto()
    STORAGE_PATH = auto()
    PASSTHROUGH_PATH = auto()


storage_schemas = ["s3:/", "gs:/"]

@dataclass
class DagshubPath:
    """
    Class for handling any path used inside the virtual filesystem

    Attributes:
        fs (DagsHubFilesystem): Filesystem from which this path is assigned
        absolute_path (Path): Absolute path in the system
        relative_path (Optional[Path]): Path relative to the root of the encapsulating FileSystem.
                                        If None, path is outside the FS
    """
    # TODO: this couples this class hard to the fs, need to decouple later
    fs: Any # Actual type is DagsHubFilesystem, but imports are wonky
    absolute_path: Optional[Path]
    relative_path: Optional[Path]

    def __post_init__(self):
        # Handle storage paths - translate s3:/bla-bla to .dagshub/storage/s3/bla-bla
        if self.relative_path is not None:
            str_path = self.relative_path.as_posix()
            for storage_schema in storage_schemas:
                if str_path.startswith(storage_schema):
                    str_path = str_path[len(f"{storage_schema}"):]
                    self.relative_path = Path(".dagshub/storage") / storage_schema[:-2] / str_path
                    self.absolute_path = self.fs.project_root / self.relative_path

    @cached_property
    def path_type(self):
        if self.absolute_path is None:
            return DagshubPathType.UNKNOWN
        if self.relative_path is None:
            return DagshubPathType.OUT_OF_REPO

        res = DagshubPathType.TRACKED_IN_REPO
        if self._is_storage_path():
            res |= DagshubPathType.STORAGE_PATH
        if self._is_passthrough_path():
            res |= DagshubPathType.PASSTHROUGH_PATH
        return res

    @cached_property
    def name(self):
        return self.absolute_path.name

    @cached_property
    def is_in_repo(self):
        return not (DagshubPathType.OUT_OF_REPO in self.path_type or DagshubPathType.UNKNOWN in self.path_type)

    def _is_storage_path(self):
        return self.relative_path.as_posix().startswith(".dagshub/storage")

    def _is_passthrough_path(self):
        str_path = self.relative_path.as_posix()
        if "/site-packages/" in str_path:
            return True
        return str_path.startswith(('.git/', '.dvc/')) or str_path in (".git", ".dvc")

