from pathlib import Path


class DagsHubRepoNotFoundError(Exception):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def __str__(self):
        return f"Couldn't find a DagsHub repo in the path {self.path} or its parents"
