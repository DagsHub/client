import os
import sys
from http import HTTPStatus

import click

import dagshub.auth
from dagshub.common import config
import dagshub.common.logging
import logging
import git

from dagshub.common.config import DEFAULT_HOST
from dagshub.common.helpers import http_request
from dagshub.upload import create_repo
from dagshub.upload.wrapper import DEFAULT_COMMIT_MESSAGE


@click.group()
@click.option("--host", default=config.host, help="Hostname of DagsHub instance")
@click.pass_context
def cli(ctx, host):
    dagshub.common.logging.init_logger()
    ctx.obj = {"host": host.strip("/")}


@cli.command()
@click.argument("project_root", default=".")
@click.option("--repo_url", help="URL of the repo hosted on DagsHub")
@click.option("--branch", help="Repository's branch")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.option(
    "--debug", default=False, type=bool, help="Run fuse in foreground"
)
# todo: add log level
@click.pass_context
def mount(ctx, verbose, **kwargs):
    """
    Mount a DagsHub Storage folder via FUSE
    """
    # Since pyfuse can crash on init-time, import it here instead of up top
    from dagshub.streaming import mount

    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    if not kwargs["debug"]:
        # Hide tracebacks of errors, display only error message
        sys.tracebacklimit = 0
    mount(**kwargs)


@cli.command()
@click.option("--token", help="Login using a specified token")
@click.option("--host", help="DagsHub instance to which you want to login")
@click.pass_context
def login(ctx, token, host):
    """
    Initiate an Oauth authentication process. This process will generate and cache a short-lived token in your
    local machine, to allow you to perform actions that require authentication. After running `dagshub login` you can
    use data streaming and upload files without providing authentication info.
    """
    host = host or ctx.obj["host"]
    if token is not None:
        dagshub.auth.add_app_token(token, host)
        print("Token added successfully")
    else:
        dagshub.auth.add_oauth_token(host)
        print("OAuth token added")


def validate_repo(ctx, param, value):
    parts = value.split("/")
    if len(parts) != 2:
        raise click.BadParameter("repo needs to be in the format <repo-owner>/<repo-name>")
    return tuple(parts)


def to_log_level(verbosity):
    if verbosity == 0:
        return logging.WARN
    elif verbosity == 1:
        return logging.INFO
    elif verbosity >= 2:
        return logging.DEBUG


@cli.command()
@click.argument("repo", callback=validate_repo)
@click.argument("filename", type=click.Path(exists=True))
@click.argument("target")
@click.option("-m", "--message", help="Commit message for the upload")
@click.option("-b", "--branch", help="Branch to upload the file to")
@click.option("--update", is_flag=True, help="Force update an existing file")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.pass_context
def upload(ctx,
           filename,
           target,
           repo,
           message,
           branch,
           verbose,
           update,
           **kwargs):
    """
    Upload FILENAME to REPO at location TARGET.
    REPO should be of the form <owner>/<repo-name>, i.e nirbarazida/yolov6.
    TARGET should include the full path inside the repo, including the filename itself.
    """
    from dagshub.upload import Repo
    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    owner, repo_name = repo
    repo = Repo(owner=owner, name=repo_name, branch=branch)
    try:
        repo.upload(file=filename, path=target, commit_message=message, force=update)
    except RuntimeError as re:
        # if uploaded filename already exists but update is False, a strange error message will appear
        # since gogs tries to check last commit in this case
        if "invalid last_commit" in str(re):
            raise RuntimeError('Verify that the uploaded file is new') from re
        else:
            raise re


@cli.command()
@click.argument("repo", callback=validate_repo)
@click.option("-u", "--upload-data", help="Upload data from specified url to new repository")
@click.option("-c", "--clone", is_flag=True,  help="Clone repository locally")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
def repo_create(
                repo,
                upload_data,
                clone,
                verbose):
    """
    repo_create
    example:  dagshub repo-create sdafni.yd/yuvtutorial14 -u "http://0.0.0.0:8080/index.html" --checkout
    """
    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    owner, repo_name = repo
    INITIAL_DATA_FILE_NAME = 'repo_created_initial_data'

    #
    # create the repo in dagshub
    #
    repo = create_repo(repo_name)
    logger.info(f"Created repo: {DEFAULT_HOST}/{owner}/{repo_name}.git")

    if clone:
        #
        # clone locally
        #
        git.Git(repo_name).clone(f"{DEFAULT_HOST}/{owner}/{repo_name}.git")
        logger.info(f"Cloned repo to folder {repo_name}")

    if upload_data:
        #
        # get data file,
        # if repo was cloned - copy the file to local location, commit and push to repo.
        # if not - upload using gogs api, and delete the local copy
        #
        res = http_request("GET", upload_data)
        if res.status_code != HTTPStatus.OK:
            raise RuntimeError(f"Could not get file from source (response: {res.status_code}), repo created")

        with open(INITIAL_DATA_FILE_NAME, 'w+') as fh:
            fh.write(res.text)

        if clone:
            os.rename(INITIAL_DATA_FILE_NAME, f"{repo_name}/{INITIAL_DATA_FILE_NAME}")
            local_repo = git.Repo(repo_name)
            local_repo.git.add('--all')
            local_repo.git.commit('-m', DEFAULT_COMMIT_MESSAGE)
            origin = local_repo.remote(name='origin')
            origin.push()
            logger.info(f"Data file named {INITIAL_DATA_FILE_NAME} committed and pushed to repo")
        else:
            repo.upload(file=INITIAL_DATA_FILE_NAME)
            os.remove(INITIAL_DATA_FILE_NAME)
            logger.info(f"Data file named {INITIAL_DATA_FILE_NAME} uploaded to repo")





