#!/usr/bin/env python3

import tempfile
from IPython import get_ipython
from dagshub.upload import Repo

def save(filename, path, repo_owner, repo_name, branch, commit_message='added a notebook', versioning='git') -> None:
    with tempfile.TemporaryDirectory() as tmp:
        get_ipython().run_line_magic('notebook', f'{tmp}/{filename}')
        repo = Repo(repo_owner, repo_name, branch)
        repo.last_commit = repo._get_last_commit()
        repo.upload(f'{tmp}/{filename}', remote_path=f'{path}/{filename}', commit_message=commit_message, versioning=versioning)
