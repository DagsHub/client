import httpx

from ..upload.wrapper import create_repo
from dagshub.common import config
from pathlib import Path
import shutil
import urllib
import os

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
    return httpx.request(method, url, **kwargs)

def init(repo_name, repo_owner, host='https://dagshub.com/'):
    import dagshub.auth
    from dagshub.auth.token_auth import HTTPBearerAuth

    username = config.username
    password = config.password
    if username is not None and password is not None:
        auth = username, password
    else:
        token = config.token or dagshub.auth.get_token()
        if token is not None:
            auth = token, token
            bearer = HTTPBearerAuth(token)
    uri = urllib.parse.urljoin(host, repo_owner, repo_name)

    res = http_request("GET", urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=repo_owner,
        reponame=repo_name)), auth=bearer or auth)
    if res.getcode() == 404: create_repo(repo_name, repo_owner)

    # MLFlow environment variables
    os.environ['MLFLOW_TRACKING_URI'] = f'{uri}.mlflow'
    os.environ['MLFLOW_TRACKING_USERNAME'] = auth[0]
    os.environ['MLFLOW_TRACKING_PASSWORD'] = auth[1]

    # DVC
    res = http_request("GET", urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=repo_owner,
        reponame=repo_name)), auth=bearer or auth)
    conf_path = Path(__file__).parent.parent.as_posix(), 'etc', 'config'),
    shutil.copyfile(os.path.join(Path(__file__).parent.parent.as_posix(), 'etc', 'config.template'), conf_path)

    with open(conf_path, 'a') as conf: conf.write(f'[\'remote "{remote}"\']\n    url = {uri}.dvc')

    print('Repository initialized!')
