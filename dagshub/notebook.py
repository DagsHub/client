import datetime
import json
import logging
import tempfile
from pathlib import Path, PurePosixPath
from socket import gethostname, gethostbyname
from typing import TYPE_CHECKING

import httpx
import urllib.parse

from dagshub.common.util import lazy_load
from dagshub.common.helpers import log_message
from dagshub.upload import Repo

if TYPE_CHECKING:
    import IPython as IPy
else:
    IPy = lazy_load("IPython")


logger = logging.getLogger(__name__)


def _inside_notebook():
    return IPy.get_ipython() is not None


def _inside_colab():
    try:
        if IPy.get_ipython() and "google.colab" in IPy.get_ipython().extension_manager.loaded:
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


def save_notebook(repo, path="", branch=None, commit_message=None, versioning="git", colab_timeout=40) -> None:
    """
    Save the notebook to DagsHub.

    Args:
        repo: Repository in the format of ``user/repo``.
        path: Path of the notebook in repo, including the filename.
             If left empty, saves the notebook to the root of the repo with format ``notebook-{date.now}.ipynb``.
             If path is a directory and not a file (no extension), saves it to ``path/notebook-{date.now}.ipynb``.
        branch: The branch under which to save the notebook. Uses the repo default if not specified.
        commit_message: Message of the commit with the notebook upload. Default is ``"Uploaded notebook {name}"``
        versioning: Either ``"git"`` or ``"dvc"``.
        colab_timeout: For Colab environments sets the timeout for getting the notebook (in seconds).
            Raise this if you have a large notebook and encountering timeouts while saving it.


    .. note::
        Right now correctly saves only notebooks in a Colab environment.
        Regular Jupyter environment will have the execution history saved instead of the notebook.
    """

    if not _inside_notebook():
        log_message(
            "Trying to save a notebook while not being in an IPython environment. No notebook will be saved", logger
        )
        return

    # Handle file path
    file_path = Path(path)
    if file_path.name != "." and "." not in file_path.name:
        file_path /= _default_notebook_name()
    file_path = "/" / file_path
    remote_path = PurePosixPath("/") / file_path.as_posix()

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

            notebook_ipynb = _message.blocking_request("get_ipynb", timeout_sec=colab_timeout)
            if notebook_ipynb is None or "ipynb" not in notebook_ipynb:
                raise RuntimeError("Couldn't get notebook data from colab.")
            with open(out_path, "w") as file:
                file.write(json.dumps(notebook_ipynb["ipynb"], indent=4))
        else:
            log_message("Saving only the execution history for the notebook in Jupyter environments", logger)
            IPy.get_ipython().run_line_magic("notebook", out_path)

        repo = Repo(owner, repo, branch=branch)
        repo.upload(
            out_path,
            remote_path=remote_path.as_posix(),
            commit_message=commit_message,
            versioning=versioning,
            force=True,
        )
