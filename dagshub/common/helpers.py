import logging
import urllib
from os.path import ismount
from pathlib import Path

import httpx

from dagshub.common import config, rich_console

default_logger = logging.getLogger("dagshub")


def get_default_branch(owner, reponame, auth, host=config.host):
    """
    The get_default_branch function returns the default branch of a given repository.

    Args:
        owner (str): Specify the owner of the repository
        reponame (str): Specify the name of the repository
        auth (Any): Authentication object or a (username, password) tuple
        host (str, optional): Specify the host to be used. Defaults to config.host.

    Returns:
        The default branch of the given repository
    """
    res = http_request(
        "GET",
        urllib.parse.urljoin(
            host,
            config.REPO_INFO_URL.format(
                owner=owner,
                reponame=reponame,
            ),
        ),
        auth=auth,
    )
    return res.json().get("default_branch")


def http_request(method, url, **kwargs):
    """
    Perform an HTTP request using the specified method and URL.

    Args:
        method (str): The HTTP method (e.g., 'GET', 'POST') for the request.
        url (str): The URL to send the HTTP request to.

    Returns:
        httpx.Response: The HTTP response object containing the result of the request.
    """
    mixin_args = {"timeout": config.http_timeout, "follow_redirects": True}
    # Set only if it's not set previously
    for arg in mixin_args:
        if arg not in kwargs:
            kwargs[arg] = mixin_args[arg]
    # Add the config headers to the headers being sent out
    headers = kwargs.get("headers", {})
    headers.update(config.requests_headers)
    kwargs["headers"] = headers
    return httpx.request(method, url, **kwargs)


def get_project_root(root):
    while not (root / ".git").is_dir():
        if ismount(root):
            raise ValueError(
                f"No git project found! (stopped at mountpoint {root}). \
                               Please run this command in a git repository."
            )
        root = root / ".."
    return Path(root)


def sizeof_fmt(num, suffix="B"):
    """
    Shoutout to https://stackoverflow.com/a/1094933
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def prompt_user(prompt, default=False) -> bool:
    """
    Prompt the user for input.
    Asks them the provided prompt + Are you sure [letters].
    Default value can be specified with the `default` args.
    """
    prompt_letters = "[y/(N)]" if not default else "[(Y)/n]"
    prompt += f"\nAre you sure {prompt_letters}: "

    prompt_response = input(prompt).lower()
    if prompt_response not in ["y", "n"]:
        return default
    return prompt_response == "y"


def log_message(msg, logger=None):
    """
    Logs message to the info of the logger + prints, unless the printing was suppressed
    """
    if not config.quiet:
        rich_console.print(msg)
    logger = logger or default_logger
    logger.info(msg)
