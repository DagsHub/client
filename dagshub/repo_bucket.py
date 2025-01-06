from typing import Literal

from dagshub.common.api.repo import RepoAPI
from dagshub.auth import get_token
from dagshub.common.helpers import log_message


def get_boto_client(repo_api: RepoAPI, token: str):
    """
    Creates a `boto3.client \
        <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/boto3.html#boto3.client>`_.\
    object to interact with the bucket of the repository.

    `Read the boto3 docs for more <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html>`_

    :meta private:
    """
    endpoint_url = repo_api.repo_bucket_api_url()
    import boto3

    client = boto3.client("s3", endpoint_url=endpoint_url, aws_access_key_id=token, aws_secret_access_key=token)
    log_message(f"Client created. Use the name of the repo ({repo_api.repo_name}) as the name of the bucket")
    return client


def get_s3fs_client(repo_api: RepoAPI, token: str):
    """
    Creates an `s3fs.S3FileSystem <https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem>`_\
    object to interact with the bucket of the repository

    `Read the s3fs docs for more <https://s3fs.readthedocs.io/en/latest/index.html#examples>`_

    :meta private:
    """
    endpoint_url = repo_api.repo_bucket_api_url()
    import s3fs

    client = s3fs.S3FileSystem(endpoint_url=endpoint_url, key=token, secret=token)
    log_message(f"Client created. Use the name of the repo ({repo_api.repo_name}) as the name of the bucket")
    return client


_s3_flavor_lookup = {
    "boto": get_boto_client,
    "s3fs": get_s3fs_client,
}

FlavorTypes = Literal["boto", "s3fs"]


def get_repo_bucket_client(repo: str, flavor: FlavorTypes = "boto"):
    """
    Creates an S3 client for the specified repository's DagsHub storage bucket

    Available flavors are:
        ``"boto"`` (Default): Returns a `boto3.client \
        <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html>`_.\
            with predefined EndpointURL and credentials.
            The name of the bucket is the name of the repository,
            and you will need to specify it for any request you make.

            Example usage::

                boto_client = get_repo_bucket_client("user/my-repo")

                # Upload file
                boto_client.upload_file(
                    Bucket="my-repo",      # name of the repo
                    Filename="local.csv",  # local path of file to upload
                    Key="remote.csv",      # remote path where to upload the file
                )
                # Download file
                boto_client.download_file(
                    Bucket="my-repo",      # name of the repo
                    Key="remote.csv",      # remote path from where to download the file
                    Filename="local.csv",  # local path where to download the file
                )


        ``"s3fs"``: Returns a \
            `s3fs.S3FileSystem <https://s3fs.readthedocs.io/en/latest/index.html#examples>`_\
             with predefined EndpointURL and credentials.
              The name of the bucket is the name of the repository,
              and you will need to specify it for any request you make

              Example usage::

                s3fs_client = get_repo_bucket_client("user/my-repo", flavor="s3fs")

                # Read from file
                with s3fs_client.open("my-repo/remote.csv", "rb") as f:
                    print(f.read())

                # Write to file
                with s3fs_client.open("my-repo/remote.csv", "wb") as f:
                    f.write(b"Content")

                # Upload file (can also upload directories)
                s3fs_client.put(
                    "local.csv",           # local path of file/dir to upload
                     "my-repo/remote.csv"  # remote path where to upload the file
                )



    Args:
        repo: Name of the repo in the format of ``username/reponame``
        flavor: one of the possible s3 client flavor variants
    """
    repo_api = RepoAPI(repo)
    token = get_token()
    return _s3_flavor_lookup[flavor](repo_api, token)
