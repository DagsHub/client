from pathlib import Path


class FilesystemAlreadyMountedError(Exception):
    def __init__(self, path: Path, revision: str):
        self.path = path
        self.revision = revision

    def __str__(self):
        return f"Filesystem bound to revision \"{self.revision}\" is already mounted at path {self.path.absolute()}"
