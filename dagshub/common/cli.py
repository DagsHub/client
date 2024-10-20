import os
import sys
import tempfile
import shutil

import click
import logging
import git
import zipfile
import tarfile
from http import HTTPStatus
from urllib.parse import urlparse

import dagshub.auth
import dagshub.common.logging_util
from dagshub import init, __version__
from dagshub.common import config, rich_console
from dagshub.common.api.repo import RepoAPI
from dagshub.upload import create_repo, Repo
from dagshub.common.helpers import http_request, log_message
from dagshub.upload.errors import UpdateNotAllowedError
from dagshub.upload.wrapper import add_dataset_to_repo, DEFAULT_DATA_DIR_NAME

_dagshub_bucket_doc_link = "https://dagshub.com/docs/feature_guide/dagshub_storage/"


@click.group()
@click.option("--host", default=config.host, help="Hostname of DagsHub instance")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.pass_context
def cli(ctx, host, quiet):
    dagshub.common.logging_util.init_logger()
    ctx.obj = {"host": host.strip("/"), "quiet": quiet or config.quiet}


@cli.command()
@click.argument("project_root", default=".")
@click.option("--repo_url", help="URL of the repo hosted on DagsHub")
@click.option("--branch", help="Repository's branch")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.option("--debug", default=False, type=bool, help="Run fuse in foreground")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.pass_context
def mount(ctx, verbose, quiet, **kwargs):
    """
    Mount a DagsHub Storage folder via FUSE
    """
    # Since pyfuse can crash on init-time, import it here instead of up top
    from dagshub.streaming import mount

    config.quiet = ctx.obj["quiet"] or quiet

    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    if not kwargs["debug"]:
        # Hide tracebacks of errors, display only error message
        sys.tracebacklimit = 0
    mount(**kwargs)


@cli.group()
@click.pass_context
def setup(ctx):
    """
    Initialize additional functionality in the current repository
    """
    pass


@setup.command("dvc")
@click.option("--repo_name", help="The repository name to set up")
@click.option("--repo_owner", help="Owner of the repository in use (user or organization)")
@click.option("--url", help="DagsHub remote url; either provide --url or repo_name and repo_owner")
@click.option(
    "--host",
    default=config.DEFAULT_HOST,
    help="DagsHub instance to which you want to login",
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.pass_context
def setup_dvc(ctx, quiet, repo_name, repo_owner, url, host):
    """
    Initialize dvc
    """
    host = host or ctx.obj["host"]
    config.quiet = quiet or ctx.obj["quiet"]
    init(
        repo_name=repo_name,
        repo_owner=repo_owner,
        url=url,
        root=None,
        host=host,
        mlflow=False,
        dvc=True,
    )


@cli.command()
@click.option("--token", help="Login using a specified token")
@click.option("--host", help="DagsHub instance to which you want to login")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.pass_context
def login(ctx, token, host, quiet):
    """
    Initiate an Oauth authentication process. This process will generate and cache a short-lived token in your
    local machine, to allow you to perform actions that require authentication. After running `dagshub login` you can
    use data streaming and upload files without providing authentication info.
    """
    host = host or ctx.obj["host"]
    config.quiet = quiet or ctx.obj["quiet"]
    if token is not None:
        dagshub.auth.add_app_token(token, host)
        rich_console.print(":white_check_mark: Token added successfully")
    else:
        dagshub.auth.add_oauth_token(host)
        rich_console.print(":white_check_mark: OAuth token added")


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


KEEP_PREFIX_HELP = """ Whether to keep the path of the folder in the download path or not.
Example: Given remote_path "src/data" and file "test/file.txt"
if True: will download to "<local_path>/src/data/test/file.txt"
if False: will download to "<local_path>/test/file.txt"
"""


@cli.command()
@click.argument("repo", callback=validate_repo)
@click.argument("remote_path")
@click.argument("local_path", required=False, type=click.Path())
@click.option(
    "-b",
    "--branch",
    help="Branch or revision to download from. " "If left unspecified, use the default branch.",
)
@click.option("--keep-prefix", is_flag=True, default=False, help=KEEP_PREFIX_HELP)
@click.option("--not-recursive", is_flag=True, help="Don't download nested folders")
@click.option(
    "--redownload",
    is_flag=True,
    help="Redownload files, even if they already exist locally",
)
@click.option(
    "--download-storages",
    is_flag=True,
    default=False,
    help="[Valid only when remote_path is '/'] Download integrated storage buckets as well as the repo content",
)
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.option("--host", help="DagsHub instance to which you want to login")
@click.option(
    "--bucket",
    is_flag=True,
    help="\b\nDownload the file(s) from the repo's DagsHub Storage bucket."
    "\nMakes it so remote path is relative to the root of the storage bucket"
    f"\nLearn more about the repo bucket here: {_dagshub_bucket_doc_link}",
)
@click.pass_context
def download(
    ctx,
    repo,
    remote_path,
    local_path,
    branch,
    not_recursive,
    keep_prefix,
    verbose,
    quiet,
    host,
    redownload,
    download_storages,
    bucket,
):
    """
    Download REMOTE_PATH from REPO to LOCAL_PATH

    REMOTE_PATH can be either directory or a file

    If LOCAL_PATH is left blank, downloads to the current directory

    Example:
        dagshub download nirbarazida/CheXNet data_labeling/data ./data
    """
    host = host or ctx.obj["host"]
    config.quiet = quiet or ctx.obj["quiet"]

    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    repoApi = RepoAPI(f"{repo[0]}/{repo[1]}", host=host)

    if bucket:
        remote_path = f"s3:/{repoApi.repo_name}/{remote_path.lstrip('/')}"

    repoApi.download(
        remote_path,
        local_path,
        revision=branch,
        recursive=not not_recursive,
        keep_source_prefix=keep_prefix,
        redownload=redownload,
        download_storages=download_storages,
    )


@cli.command()
@click.argument("repo", callback=validate_repo)
@click.argument("filename", type=click.Path(exists=True))
@click.argument("target", required=False)
@click.option("-m", "--message", help="Commit message for the upload")
@click.option("-b", "--branch", help="Branch to upload the file to")
@click.option("--update", is_flag=True, help="Force update existing files/directories")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.option("--host", help="DagsHub instance to which you want to login")
@click.option(
    "--versioning",
    help="Versioning system to be used to upload the file(s)",
    type=click.Choice(["git", "dvc", "auto"]),
)
@click.option(
    "--bucket",
    is_flag=True,
    help="\b\nUpload the file(s) to the repo's DagsHub Storage bucket (s3-compatible)"
    f"\nLearn more about the repo bucket here: {_dagshub_bucket_doc_link}",
)
@click.pass_context
def upload(
    ctx,
    filename,
    target,
    repo,
    message,
    branch,
    verbose,
    update,
    quiet,
    host,
    versioning,
    bucket,
    **kwargs,
):
    """
    Upload FILENAME to REPO at location TARGET.

    FILENAME can be a directory.

    REPO should be of the form <owner>/<repo-name>, e.g: nirbarazida/yolov6.

    TARGET should include the full path inside the repo, including the filename itself.
    If TARGET is omitted, it defaults to using the relative path to FILENAME from current working directory,
    or the filename itself if it's not relative to the current working directory.
    """
    config.host = host or ctx.obj["host"] or config.host
    config.quiet = quiet or ctx.obj["quiet"]

    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    owner, repo_name = repo
    repo = Repo(owner=owner, name=repo_name, branch=branch)
    try:
        repo.upload(
            local_path=filename,
            remote_path=target,
            commit_message=message,
            bucket=bucket,
            force=update,
            versioning=versioning,
        )
    except UpdateNotAllowedError:
        log_message(
            ":warning: You're trying to update existing files! :warning:\n"
            "If you want to do that, retry with --update to force the update",
            logger,
        )


@cli.command()
def version():
    """
    Prints the current installed version of the DagsHub client
    """
    print(__version__)


@cli.group()
def repo():
    """
    Operations on repo: currently only 'create'
    """
    pass


@repo.command()
@click.argument("repo_name")
@click.option("-u", "--upload-data", help="Upload data from specified url to new repository")
@click.option("-c", "--clone", is_flag=True, help="Clone repository locally")
@click.option("-v", "--verbose", default=0, count=True, help="Verbosity level")
@click.option("-q", "--quiet", is_flag=True, help="Suppress print output")
@click.pass_context
def create(ctx, repo_name, upload_data, clone, verbose, quiet):
    """
    create a repo and:\n
    optional- upload files to 'data' dir,
     .zip and .tar files are extracted, other formats copied as is.
    optional- clone repo locally.\n
    example 1:  dagshub repo create mytutorial -u "http://example.com/data.csv" --clone\n
    example 2:  dagshub --host "https://www.dagshub.com"
                    repo create mytutorial2 -u "http://0.0.0.0:8080/index.html" --clone --verbose
    """

    config.quiet = quiet or ctx.obj["quiet"]

    logger = logging.getLogger()
    logger.setLevel(to_log_level(verbose))

    with tempfile.TemporaryDirectory() as tmp_dir:
        # override default host if provided by --host
        host = ctx.obj["host"]

        # create remote repo
        repo = create_repo(repo_name, host=host)
        log_message(f"Created repo: {host}/{repo.owner}/{repo.name}.git", logger)

        if upload_data:
            # get the data
            res = http_request("GET", upload_data)
            if res.status_code != HTTPStatus.OK:
                raise RuntimeError(f"Could not get file from source (response: {res.status_code}), repo created")

            downloaded_file_name = os.path.basename(urlparse(upload_data).path)

            # save to disk
            with open(downloaded_file_name, "wb") as fh:
                fh.write(res.content)

            log_message(f"Downloaded and saved {downloaded_file_name}", logger)

            # extract to data dir or move there
            if zipfile.is_zipfile(downloaded_file_name):
                with zipfile.ZipFile(downloaded_file_name, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)
            elif tarfile.is_tarfile(downloaded_file_name):
                with tarfile.TarFile(downloaded_file_name, "r") as tar_ref:
                    tar_ref.extractall(tmp_dir)
            else:
                shutil.move(downloaded_file_name, f"{tmp_dir}/{downloaded_file_name}")

            # upload data dir as DVC to repo
            add_dataset_to_repo(repo, tmp_dir, DEFAULT_DATA_DIR_NAME)
            log_message("Data uploaded to repo", logger)

        if clone:
            # make local repo
            git.Git(repo.name).clone(f"{host}/{repo.owner}/{repo.name}.git")
            log_message(f"Cloned repo to folder {repo.name}", logger)

            # move the data to it,
            # now the local repo resembles the remote but with copy of data
            if upload_data:
                shutil.move(tmp_dir, f"{repo.name}/{DEFAULT_DATA_DIR_NAME}")
                log_message(f"files moved to {repo.name}/{DEFAULT_DATA_DIR_NAME}", logger)

    # clean tmp file/dir if exists
    if upload_data and os.path.exists(downloaded_file_name):
        os.remove(downloaded_file_name)


if __name__ == "__main__":
    cli()
