from pathlib import Path


class FilesystemAlreadyMountedError(Exception):
    def __init__(self, path: Path, repo: str, revision: str):
        self.path = path
        self.repo = repo
        self.revision = revision

    def __str__(self):
        return (
            f"There is already a filesystem mounted at path {self.path.absolute()} "
            f"({self.repo} revision {self.revision})"
            f"\nrun dagshub.streaming.uninstall_hooks({self.path.absolute()}) to remove the existing hook"
        )
