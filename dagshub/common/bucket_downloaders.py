from typing import Tuple, Callable

import regex

storage_download_url_regex = regex.compile(
    r".*/api/v1/repos/(?P<user>[\w\-_.]+)/(?P<repo>[\w\-_.]+)/storage/raw/(s3|gcs)/"
    r"(?P<bucket>[a-z0-9.-]+)/(?P<path>.*)")


def download_url_to_bucket_path(path: str) -> Tuple[str, str]:
    """
    Gets a storage download URL of a dagshub file, returns a pair of (bucket, path_in_bucket)
    """
    matches = storage_download_url_regex.match(path)
    if matches is None:
        raise ValueError(f"Path {path} is not a storage path")
    groups = matches.groupdict()
    return groups["bucket"], groups["path"]


def enable_gcs_bucket_downloader(client):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    Client is assumed to be a client from the `google-cloud-storage` package

    For other clients use `enable_custom_bucket_downloader` function
    """
    raise NotImplementedError


def enable_s3_bucket_downloader(client):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    Client is assumed to be a boto3 client.

    For other clients use `enable_custom_bucket_downloader` function
    """
    raise NotImplementedError


def enable_custom_bucket_downloader(function: Callable[[str, str], bytes]):
    """
    Enables downloading storage items using a custom function
    The function must receive two arguments: bucket name and a path, and returns the binary of the downloaded file
    """
    raise NotImplementedError
