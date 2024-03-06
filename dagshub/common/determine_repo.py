import urllib.parse
from pathlib import Path
from typing import Optional, Union, Tuple

from dagshub.common import config
from dagshub.common.api import RepoAPI
from dagshub.common.errors import DagsHubRepoNotFoundError
from dagshub.common.util import lazy_load

git = lazy_load("git")


def parse_dagshub_remote(remote_url: urllib.parse.ParseResult, host_url: urllib.parse.ParseResult) -> Optional[str]:
    """
    Tries to parse the remote url, extracting the name of a DagsHub repo from it and returning it

    Args:
        remote_url: parsed URL of the remote
        host_url: parsed URL of the DagsHub host

    Returns:
        Repository name in the `<user>/<repo>` format
    """
    if remote_url.hostname != host_url.hostname:
        return None

    # Check for the host prefix and the path ending with .git
    if not (remote_url.path.startswith(host_url.path) and remote_url.path.endswith(".git")):
        return None

    subpath = remote_url.path[len(host_url.path) :]
    # Should leave the subpath of the host, if the remote is correct it should be just "/user/repo.git"
    subpath = subpath.lstrip("/")
    if subpath.count("/") > 1:
        return None
    return subpath[: -len(".git")]


def determine_repo(path: Optional[Union[str, Path]] = None, host: Optional[str] = None) -> Tuple[RepoAPI, str]:
    """
    Tries to find a DagsHub repository in the specified path by traversing up the tree
    and looking for a git repo with the DagsHub remote.

    Args:
        path: Path where to look for the repo. If None, looks in current working directory
        host: DagsHub host, defaults to https://dagshub.com

    Returns:
        RepoAPI object of the repo + name of the current branch
    """
    if path is None:
        path = Path.cwd()
    else:
        path = Path(path)

    if host is None:
        host = config.host

    try:
        repo = git.Repo(path, search_parent_directories=True)
    except git.InvalidGitRepositoryError as ex:
        raise DagsHubRepoNotFoundError(path) from ex

    repo_name: Optional[str] = None
    host_url = urllib.parse.urlparse(host)
    for remote in repo.remotes:
        repo_name = parse_dagshub_remote(urllib.parse.urlparse(remote.url), host_url)
        if repo_name is not None:
            break

    if repo_name is None:
        raise DagsHubRepoNotFoundError(path)

    return RepoAPI(repo_name, host=host), repo.active_branch.name
