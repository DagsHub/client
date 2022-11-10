from dagshub.common import config
import urllib
import requests

def get_default_branch(owner, reponame, auth):
    res = requests.get(urllib.parse.urljoin(config.host, config.REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')