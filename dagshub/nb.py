#!/usr/bin/env python3

import json
import tempfile
from IPython import get_ipython
from dagshub.upload import Repo


def _inside_colab():
    try:
        if get_ipython() and 'google.colab' in get_ipython().extension_manager.loaded:
            return True
    except Exception:
        pass
    return False


def save(filename, path, repo_owner, repo_name, branch, commit_message='added a notebook', versioning='git') -> None:
    """
    IPython wrapper for saving notebooks.

    :param filename (str): The name of the file under which the notebook should be saved
    :param path (str): The path within the remote where the notebook should be saved
    :param repo_owner (str): The username of the user who owns this repository
    :param repo_name (str): Identify the repository
    :param branch (str): The branch under which the notebook should be saved
    :param commit_message (str): The commit message for the update
    :param versioning (str): ['git'|'dvc'] The VCS used to version the notebook
    """

    with tempfile.TemporaryDirectory() as tmp:
        if _inside_colab():
            from google.colab import _message  # If inside colab, this import is guaranteed
            with open(f'{tmp}/{filename}', 'w') as file:
                file.write(json.dumps(_message.blocking_request('get_ipynb'), indent=4))
        else:
            get_ipython().run_line_magic('notebook', f'{tmp}/{filename}')

        repo = Repo(repo_owner, repo_name, branch)
        repo.last_commit = repo._get_last_commit()
        repo.upload(f'{tmp}/{filename}',
                    remote_path=f'{path}/{filename}',
                    commit_message=commit_message,
                    versioning=versioning)
