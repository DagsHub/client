import datetime
import json
import logging
import tempfile
from pathlib import PosixPath
from socket import gethostname, gethostbyname

import httpx
import urllib.parse
from IPython import get_ipython

from dagshub.common.helpers import log_message
from dagshub.upload import Repo

logger = logging.getLogger(__name__)


def _inside_notebook():
    return get_ipython() is not None


def _inside_colab():
    try:
        if get_ipython() and 'google.colab' in get_ipython().extension_manager.loaded:
            return True
    except Exception:
        pass
    return False


def _default_notebook_name():
    if _inside_colab():
        # Shout out to https://stackoverflow.com/a/61906730
        ip = gethostbyname(gethostname())
        filename = httpx.get(f"http://{ip}:9000/api/sessions").json()[0]["name"]
        filename = urllib.parse.unquote(filename)
        if not filename.endswith(".ipynb"):
            filename = filename + ".ipynb"
        return filename
    return f"notebook-{datetime.datetime.utcnow().strftime('%Y-%m-%d')}.ipynb"


def save_notebook(repo, path="", branch=None, commit_message=None, versioning='git') -> None:
    """
    IPython wrapper for saving notebooks.

    :param path (str): Where to save the notebook within the repository (including the filename).
        If filename is not specified, we'll save it as "notebook-{datetime.now}.ipynb" under specified folder
    :prama repo (str): repository in the format of "user/repo"
    :param branch (str): The branch under which the notebook should be saved.
        Will commit to the default repo branch if not specified
    :param commit_message (str): The commit message for the update
    :param versioning (str): ['git'|'dvc'] The VCS used to version the notebook
    """

    if not _inside_notebook():
        log_message('Trying to save a notebook while not being in an IPython environment. No notebook will be saved',
                    logger)
        return

    # Handle file path
    file_path = PosixPath(path)
    if file_path.name != "." and "." not in file_path.name:
        file_path /= _default_notebook_name()
    file_path = "/" / file_path

    # Handle commit message
    if commit_message is None:
        commit_message = f"Uploaded notebook {file_path.name}"

    # Handle repo name
    parsed_repo = repo.split("/")
    if len(parsed_repo) != 2:
        raise RuntimeError(f'Repo format has to be "user/repo" (got {repo})')
    owner, repo = parsed_repo

    # Upload notebook
    with tempfile.TemporaryDirectory() as tmp:
        out_path = f"{tmp}/{file_path.name}"
        if _inside_colab():
            from google.colab import _message  # If inside colab, this import is guaranteed
            with open(out_path, 'w') as file:
                file.write(json.dumps(_message.blocking_request('get_ipynb')["ipynb"], indent=4))
        else:
            get_ipython().run_line_magic('notebook', out_path)

        repo = Repo(owner, repo, branch=branch)
        repo.upload(out_path,
                    remote_path=file_path.as_posix(),
                    commit_message=commit_message,
                    versioning=versioning,
                    force=True)
