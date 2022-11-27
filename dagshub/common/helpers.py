import httpx

from dagshub.common import config
import urllib


def get_default_branch(owner, reponame, auth, host=config.host):
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
    return httpx.request(method, url, **kwargs)
