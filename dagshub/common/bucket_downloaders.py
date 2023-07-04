import io
from io import IOBase
from pathlib import Path
from typing import Tuple, Callable, Optional

import regex

from dagshub.common.download import DownloadFunctionType

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


def enable_gcs_bucket_downloader(client=None, redownload_existing=False):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    For custom clients use `enable_custom_bucket_downloader` function

    Args:
        client: a google.cloud.storage.Client from the `google-cloud-storage` package.
            If client isn't specified, the default parameterless constructor is used
        redownload_existing: Whether to overwrite the file if it already exists on the filesystem
    """
    if client is None:
        from google.cloud import storage
        client = storage.Client()

    def get_fn(bucket_name, bucket_path) -> IOBase:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(bucket_path).download_as_bytes()
        return io.BytesIO(blob)

    enable_custom_bucket_downloader(get_fn, redownload_existing)


def enable_s3_bucket_downloader(client=None, redownload_existing=False):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    For custom clients use `enable_custom_bucket_downloader` function

    Args:
        client: a boto3 S3 client.
            If client isn't specified, the default parameterless constructor is used
        redownload_existing: Whether to download the file if it already exists on the filesystem
    """

    if client is None:
        import boto3
        client = boto3.client("s3")

    def get_fn(bucket, path) -> IOBase:
        resp = client.get_object(Bucket=bucket, Key=path)
        return resp["Body"]

    enable_custom_bucket_downloader(get_fn, redownload_existing)


bucket_downloader_func: Optional[DownloadFunctionType] = None


def enable_custom_bucket_downloader(download_func: Callable[[str, str], IOBase], redownload_existing=False):
    """
    Enables downloading storage items using a custom function
    The function must receive two arguments: bucket name and a path, and returns the IOBase of the downloaded file

    Args:
        download_func: Function that recieves a tuple of (bucket_name, path_in_bucket)
            and returns the IOBase of the bytes
        redownload_existing: Whether to redownload the file if it exists on the filesystem
    """

    def wrap_fn(download_url: str, save_path: Path):
        """
        Wrapper function that wraps the download_func into something that is usable by the parallelized downloader
        (meaning it also handles paths and writing the received file to the FS)
        """
        if not redownload_existing and save_path.exists():
            return

        bucket_name, bucket_path = download_url_to_bucket_path(download_url)
        content = download_func(bucket_name, bucket_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open("wb") as f:
            f.write(content.read())

    global bucket_downloader_func
    bucket_downloader_func = wrap_fn
