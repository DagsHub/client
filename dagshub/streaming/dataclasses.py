from dataclasses import dataclass


@dataclass
class StorageAPIResult:
    name: str
    protocol: str
    list_path: str

    @property
    def full_path(self):
        return f"{self.protocol}/{self.name}"

@dataclass
class ContentAPIResult:
    path: str
    type: str
    size: int
    hash: str
    versioning: str
    download_url: str
