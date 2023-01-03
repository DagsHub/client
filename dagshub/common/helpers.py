import httpx

from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.upload.wrapper import create_repo
from os.path import ismount, exists
from dagshub.auth import get_token
from dagshub.common import config
from pathlib import Path
import configparser
import urllib
import git
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


def get_project_root(root):
    while not (root / '.git').is_dir():
        if ismount(root):
            raise ValueError('No git project found! (stopped at mountpoint {root}). \
                             Please run this command in a git repository.')
        root = root / '..'
    return Path(root)


def init(repo_name=None, repo_owner=None, url=None, root=None,
         host=config.DEFAULT_HOST, mlflow=True, dvc=False):
    # Setup required variables
    root = root or get_project_root(Path(os.path.abspath('.')))
    if not exists(root / '.git'):
        raise ValueError('No git project found! (stopped at mountpoint {root}). \
                          Please run this command in a git repository.')

    if url and (repo_name or repo_owner):
        repo_name, repo_owner = None, None

    if not url:
        if repo_name is not None and repo_owner is not None:
            url = urllib.parse.urljoin(host, f'{repo_owner}/{repo_name}')
        else:
            for remote in git.Repo(root).remotes:
                if host in remote.url:
                    url = remote.url[:-4]
    if not url:
        raise ValueError('No host remote found! Please specify the remote using the url variable, or --url argument.')
    elif url[-4] == '.':
        url = url[:-4]

    if not (repo_name and repo_owner):
        splitter = lambda x: (x[-1], x[-2]) # noqa E721
        repo_name, repo_owner = splitter(url.split('/'))

    if None in [repo_name, repo_owner, url]:
        raise ValueError('Could not parse repository owner and name. Make sure you specify either a link \
                          to the repository with --url or a pair of --repo-owner and --repo-name')

    # Setup authentication
    bearer = None
    token = config.token or get_token()
    bearer = HTTPBearerAuth(token)

    # Configure repository
    res = http_request("GET", urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=repo_owner,
        reponame=repo_name)), auth=bearer)
    if res.status_code == 404:
        create_repo(repo_name)

    # Configure MLFlow
    if mlflow:
        os.environ['MLFLOW_TRACKING_URI'] = f'{url}.mlflow'
        os.environ['MLFLOW_TRACKING_USERNAME'] = token
        os.environ['MLFLOW_TRACKING_PASSWORD'] = token

    # Configure DVC
    if dvc:
        Path(root / '.dvc').mkdir(parents=True, exist_ok=True)
        write = True

        dvc_config = configparser.ConfigParser()
        dvc_config_local = configparser.ConfigParser()
        dvc_config.read(root / '.dvc' / 'config')
        dvc_config_local.read(root / '.dvc' / 'config.local')

        for section in dvc_config.sections():
            if 'url' in dvc_config[section] and host in dvc_config[section]['url']:
                write = False

        remote = 'dagshub' if 'origin' in dvc_config.sections() else 'origin'
        if write:
            dvc_config_local[f'\'remote "{remote}"\''] = {'auth': 'basic',
                                                          'user': token,
                                                          'password': token}
            dvc_config[f'\'remote "{remote}"\''] = {'url': f'{url}.dvc'}

            with open(root / '.dvc' / 'config', 'w') as config_file, \
                 open(root / '.dvc' / 'config.local', 'w') as config_local_file:
                dvc_config.write(config_file)
                dvc_config_local.write(config_local_file)
                print(f'Added new remote "{remote}" with url = {url}')

        if not exists(root / '.dvc' / '.gitignore'):
            with open(root / '.dvc' / '.gitignore', 'w') as config_gitignore:
                config_gitignore.write(config.CONFIG_GITIGNORE)

    print('Repository initialized!')
