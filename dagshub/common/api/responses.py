from dataclasses import dataclass
from typing import Optional, Dict, List


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
    avatar_url: str
    public_email: str
    website: str
    company: str
    description: str
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
