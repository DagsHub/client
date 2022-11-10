from dagshub.common import config
import urllib
import requests


def get_default_branch(owner, reponame, auth, host=config.host):
    res = requests.get(urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')
