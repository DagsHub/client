from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Optional, Dict, List

from functools import cached_property


@dataclass
class RepoAPIResponse:
    id: int
    owner: "UserAPIResponse"
    name: str
    full_name: str
    description: str
    private: bool
    fork: bool
    parent: Optional["RepoAPIResponse"]
    empty: bool
    mirror: bool
    size: int
    html_url: str
    ssh_url: Optional[str]
    clone_url: str
    website: Optional[str]
    stars_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    default_branch: str
    created_at: str
    updated_at: str
    permissions: Optional[Dict[str, bool]]


@dataclass
class UserAPIResponse:
    id: int
    login: str
    full_name: str
    avatar_url: Optional[str]
    public_email: Optional[str]
    website: Optional[str]
    company: Optional[str]
    description: Optional[str]
    username: str


@dataclass
class BranchAPIResponse:
    name: str
    commit: "CommitAPIResponse"


@dataclass
class CommitAPIResponse:
    id: str
    message: str
    url: str
    author: Optional["GitUser"]
    committer: Optional["GitUser"]
    added: Optional[List[str]]
    removed: Optional[List[str]]
    modified: Optional[List[str]]
    timestamp: str


@dataclass
class GitUser:
    name: str
    email: str
    username: str


@dataclass
class StorageAPIEntry:
    name: str
    protocol: str
    list_path: str

    @cached_property
    def full_path(self):
        return f"{self.protocol}/{self.name}"

    @cached_property
    def path_in_mount(self) -> PurePosixPath:
        return PurePosixPath(".dagshub/storage") / self.protocol / self.name


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


@dataclass
class StorageContentAPIResult:
    entries: List[ContentAPIEntry]
    next_token: Optional[str]
