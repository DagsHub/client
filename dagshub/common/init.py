import configparser
import os
import urllib
import urllib.parse
from os.path import exists
from pathlib import Path
from typing import Optional

from dagshub.auth import get_token
from dagshub.common import config
from dagshub.common.api import RepoAPI, UserAPI
from dagshub.common.api.repo import RepoNotFoundError
from dagshub.common.determine_repo import determine_repo
from dagshub.common.helpers import log_message
from dagshub.upload import create_repo
from dagshub.mlflow import patch_mlflow as _patch_mlflow

from dagshub.common.util import lazy_load

git = lazy_load("git")


def _sanitize_repo_url(parsed: urllib.parse.ParseResult, path: str) -> str:
    """Rebuild a url from its parsed pieces, keeping only scheme, host and path.

    Any userinfo is dropped: `url` is written into MLflow's tracking URI and
    into .dvc/config, and .dvc/config is a committed file, so a token pasted
    into the url as "https://user:token@dagshub.com/owner/repo" would end up in
    the repository. Credentials for both are set separately from the token.
    """

    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    if not parsed.scheme and not parsed.netloc:
        # A bare "owner/repo" - nothing to rebuild around.
        return path
    return urllib.parse.urlunparse((parsed.scheme, host, path, "", "", ""))


def _parse_repo_url(url: str) -> tuple:
    """Extract (url, owner, name) from a repository url.

    The owner and name are taken from the url *path*, not from the last two
    slash-separated pieces of the whole string. Splitting the whole string lets
    the hostname stand in for the owner: "https://dagshub.com/my-repo" has only
    one path segment, but its last two pieces are "dagshub.com" and "my-repo",
    which looks valid and is not.

    The url is returned alongside them, rebuilt from the same parsed segments,
    so that the value handed to MLflow and DVC agrees with the owner and name
    that were derived from it. Parsing alone is not enough: empty segments are
    skipped when reading owner and name, so without this
    "https://dagshub.com/my-org//my-repo" would yield the right pair while
    still sending a doubled slash downstream.

    A bare "owner/repo" with no scheme is still accepted, since that is a
    reasonable thing to pass.
    """

    parsed = urllib.parse.urlparse(url)
    # With no scheme, urlparse puts everything in `path`, which is what we want
    # for a bare "owner/repo"; with one, `netloc` holds the host and is skipped.
    segments = [segment for segment in parsed.path.split("/") if segment]

    if len(segments) < 2:
        # The url is reported back redacted - a raw one can carry a token in
        # its userinfo or query, and this message is likely to be logged.
        raise ValueError(
            f"Could not determine the repo owner and name from the url "
            f"{_sanitize_repo_url(parsed, parsed.path)!r}. "
            f"Expected a url of the form https://dagshub.com/<owner>/<repo>."
        )
    return _sanitize_repo_url(parsed, "/".join(segments)), segments[-2], segments[-1]


def init(
    repo_name: Optional[str] = None,
    repo_owner: Optional[str] = None,
    url: Optional[str] = None,
    root: Optional[str] = None,
    host: Optional[str] = None,
    mlflow: bool = True,
    dvc: bool = False,
    patch_mlflow: bool = False,
):
    """
    Initialize a DagsHub repository or DagsHub-related functionality.

    Initialization includes:
        1) Creates a repository on DagsHub if it doesn't exist yet.
        2) If ``dvc`` flag is set, adds the DagsHub repository as a dvc remote.
        3) If ``mlflow`` flag is set, initializes MLflow environment variables to enable logging experiments into the\
            DagsHub hosted MLflow. That means that if you call ``dagshub.init()`` in your script,\
            then any MLflow function called later in the script will log to the DagsHub hosted MLflow.

    Arguments:
        repo_name: Along with ``repo_owner`` defines the repository on DagsHub.
        repo_owner: Along with ``repo_name`` defines the repository on DagsHub.
        url: Url to the repository on DagsHub. Can be used as an alternative to ``repo_owner/repo_name`` arguments.
        root: Path to the locally hosted git repository.
            If it's not set, tries to find a repository traversing up the filesystem.
        host: Address of the DagsHub instance with the repository.
            If specified, then all request to dagshub are going to be sent to this instance.
        mlflow: Configure MLflow to log experiments to DagsHub.
        dvc: Configure a dvc remote in the repository.
        patch_mlflow: Run :func:`dagshub.mlflow.patch_mlflow` so errors while logging with MLflow don't stop execution
    """
    if host is None:
        host = config.host
    else:
        config.set_host(host)

    if root is None:
        root = os.path.abspath(".")

    # URL specified - ignore repo name and owner args, prioritize url over it
    if url is not None:
        repo_owner, repo_name = None, None

    if None in [repo_owner, repo_name] and (repo_owner is not None or repo_name is not None):
        raise AttributeError("Both repo_owner and repo_name should be set")

    # Build URL from repo owner and name
    if repo_owner and repo_name:
        url = urllib.parse.urljoin(f"{host}/", f"{repo_owner}/{repo_name}")
    else:
        if not url:
            # Try to get the url of the repo from the git repo
            repo, branch = determine_repo(root)
            url = repo.repo_url

        # Strip a trailing slash first, so that a URL copied from the browser
        # address bar doesn't shift every segment by one.
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        url, repo_owner, repo_name = _parse_repo_url(url)

    # Create the repo if it wasn't created
    repo_api = RepoAPI(f"{repo_owner}/{repo_name}", host=host)
    try:
        repo_api.get_repo_info()
    except RepoNotFoundError:
        should_create_under_org = False
        if repo_owner:
            current_user = UserAPI.get_current_user(host=host)
            should_create_under_org = repo_owner != current_user.username

        if should_create_under_org:
            log_message(f'Repository {repo_name} doesn\'t exist, creating it under organization "{repo_owner}".')
            create_repo(repo_name, org_name=repo_owner, host=host)
        else:
            log_message(f"Repository {repo_name} doesn't exist, creating it under current user.")
            create_repo(repo_name, host=host)

    # Get the token for the configs
    token = get_token(host=host)

    # Configure MLFlow
    if mlflow:
        os.environ["MLFLOW_TRACKING_URI"] = f"{url}.mlflow"
        os.environ["MLFLOW_TRACKING_USERNAME"] = UserAPI.get_user_from_token(token, host=host).username
        os.environ["MLFLOW_TRACKING_PASSWORD"] = token

        log_message(f'Initialized MLflow to track repo "{repo_owner}/{repo_name}"')

    if patch_mlflow:
        _patch_mlflow()

    # Configure DVC
    if dvc:
        git_repo = git.Repo(root, search_parent_directories=True)
        git_repo_path = Path(git_repo.git_dir)

        Path(git_repo_path / ".dvc").mkdir(parents=True, exist_ok=True)
        write = True

        dvc_config = configparser.ConfigParser()
        dvc_config_local = configparser.ConfigParser()
        dvc_config.read(git_repo_path / ".dvc" / "config")
        dvc_config_local.read(git_repo_path / ".dvc" / "config.local")

        for section in dvc_config.sections():
            if "url" in dvc_config[section] and host in dvc_config[section]["url"]:
                write = False

        remote = "dagshub" if "origin" in dvc_config.sections() else "origin"
        if write:
            dvc_config_local[f"'remote \"{remote}\"'"] = {"auth": "basic", "user": token, "password": token}
            dvc_config[f"'remote \"{remote}\"'"] = {"url": f"{url}.dvc"}

            with open(git_repo_path / ".dvc" / "config", "w") as config_file, open(
                git_repo_path / ".dvc" / "config.local", "w"
            ) as config_local_file:
                dvc_config.write(config_file)
                dvc_config_local.write(config_local_file)
                log_message(f'Added new remote "{remote}" with url = {url}')

        if not exists(git_repo_path / ".dvc" / ".gitignore"):
            with open(git_repo_path / ".dvc" / ".gitignore", "w") as config_gitignore:
                config_gitignore.write(config.CONFIG_GITIGNORE)

    log_message(f"Repository {repo_owner}/{repo_name} initialized!")
