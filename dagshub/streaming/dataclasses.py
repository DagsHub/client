from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from functools import cached_property

if TYPE_CHECKING:
    from dagshub.streaming import DagsHubFilesystem

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

    # TODO: this couples this class hard to the fs, need to decouple later
    fs: "DagsHubFilesystem"  # Actual type is DagsHubFilesystem, but imports are wonky
    absolute_path: Optional[Path]
    relative_path: Optional[Path]
    original_path: Optional[Path]

    def __post_init__(self):
        # Handle storage paths - translate s3:/bla-bla to .dagshub/storage/s3/bla-bla
        if self.relative_path is not None:
            str_path = self.relative_path.as_posix()
            for storage_schema in storage_schemas:
                if str_path.startswith(f"{storage_schema}:/"):
                    str_path = str_path[len(storage_schema) + 2 :]
                    self.relative_path = (
                        Path(".dagshub/storage") / storage_schema / str_path
                    )
                    self.absolute_path = self.fs.project_root / self.relative_path

    @cached_property
    def name(self):
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
        return self.relative_path.as_posix().startswith(".dagshub/storage")

    @cached_property
    def is_passthrough_path(self):
        """
        Is path a "passthrough" path
        A passthrough path is a path that the FS ignores when trying to look up if the file exists on DagsHub
        This includes:
            - .git and .dvc folders - that prevents accidental access to their caches.
                If you need to read with streaming from a .dvc folder (to read config for example), please pull the repo
            - Any /site-packages/ folder - if you have a venv in your repo, python will try to find packages there.
        """
        str_path = self.relative_path.as_posix()
        if "/site-packages/" in str_path or str_path.endswith("/site-packages"):
            return True
        if str_path.startswith((".git/", ".dvc/")) or str_path in (".git", ".dvc"):
            return True
        return any((self.relative_path.match(glob) for glob in self.fs.exclude_globs))

    def __truediv__(self, other):
        return DagshubPath(
            absolute_path=self.absolute_path / other,
            relative_path=self.relative_path / other,
            original_path=self.original_path / other,
            fs=self.fs,
        )
