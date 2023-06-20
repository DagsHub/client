import configparser
import os
import urllib
from os.path import exists
from pathlib import Path

import git

from dagshub.auth import get_token
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.common.helpers import get_project_root, http_request, log_message
from dagshub.upload import create_repo


def init(repo_name=None, repo_owner=None, url=None, root=None,
         host=config.host, mlflow=True, dvc=False):
    """
    Initialize a DagsHub repository.

    Initialization includes:
        1) Creates a repository on DagsHub if it doesn't exist yet
        2) If `dvc` flag is set, adds the DagsHub repository as a dvc remote
        3) If `mlflow` flag is set, initializes MLflow environment variables to enable logging experiments into the
            DagsHub hosted MLflow

    Arguments:
        root: path to the locally hosted git repository.
            If it's not set, tries to find a repository going up the folders
        repo_owner: along with `repo_name` defines the repository on DagsHub
        repo_name: along with `repo_owner` defines the repository on DagsHub
        url: url to the repository on DagsHub. Can be used as an alternative to repo_owner/repo_name arguments
        host: address of a hosted DagsHub instance
        mlflow: configure MLflow to log experiments to DagsHub
        dvc: configure a dvc remote in the repository
    """
    # Setup required variables
    if dvc:
        root = root or get_project_root(Path(os.path.abspath('.')))
        if not exists(root / '.git'):
            raise ValueError(f'No git project found! (stopped at mountpoint {root}). \
                               Please run this command in a git repository.')

    if url and (repo_name or repo_owner):
        repo_name, repo_owner = None, None

    if not url:
        if repo_name is not None and repo_owner is not None:
            url = urllib.parse.urljoin(f'{host}/', f'{repo_owner}/{repo_name}')
        elif dvc:
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
    token = config.token or get_token(host=host)
    bearer = HTTPBearerAuth(token)

    # Configure repository
    res = http_request("GET", urllib.parse.urljoin(f'{host}/', config.REPO_INFO_URL.format(
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
                log_message(f'Added new remote "{remote}" with url = {url}')

        if not exists(root / '.dvc' / '.gitignore'):
            with open(root / '.dvc' / '.gitignore', 'w') as config_gitignore:
                config_gitignore.write(config.CONFIG_GITIGNORE)

    log_message('Repository initialized!')
