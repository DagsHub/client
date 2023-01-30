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

    :param owner(str): Specify the owner of the repository
    :param reponame (str): Specify the name of the repository
    :param auth: Authentication object or a (username, password) tuple
    :param host (str): Specify the host to be used
    :return: The default branch of the given repository
    """
    res = http_request("GET", urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')


def http_request(method, url, **kwargs):
    mixin_args = {
        "timeout": config.http_timeout,
        "follow_redirects": True
    }
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
    while not (root / '.git').is_dir():
        if ismount(root):
            raise ValueError('No git project found! (stopped at mountpoint {root}). \
                             Please run this command in a git repository.')
        root = root / '..'
    return Path(root)


def log_message(msg, logger=None):
    """
    Logs message to the info of the logger + prints, unless the printing was suppressed
    """
    if not config.quiet:
        rich_console.print(msg)
    logger = logger or default_logger
    logger.info(msg)
