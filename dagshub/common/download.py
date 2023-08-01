import logging
import os.path
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Tuple, Callable, Optional, List, Union, Dict

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import re
import rich.progress

from dagshub.auth import get_token
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.common.helpers import http_request
from dagshub.common.rich_util import get_rich_progress

logger = logging.getLogger(__name__)

DownloadFunctionType = Callable[[str, Path], None]

storage_download_url_regex = re.compile(
    r".*/api/v1/repos/(?P<user>[\w\-_.]+)/(?P<repo>[\w\-_.]+)/storage/raw/(?P<proto>s3|gs)/"
    r"(?P<bucket>[a-z0-9.-]+)/(?P<path>.*)")


def enable_gcs_bucket_downloader(client=None):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    For custom clients use `enable_custom_bucket_downloader` function

    Args:
        client: a google.cloud.storage.Client from the `google-cloud-storage` package.
            If client isn't specified, the default parameterless constructor is used
    """
    if client is None:
        from google.cloud import storage
        client = storage.Client()

    def get_fn(bucket_name, bucket_path) -> bytes:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(bucket_path).download_as_bytes()
        return blob

    add_bucket_downloader("gs", get_fn)


def enable_s3_bucket_downloader(client=None):
    """
    Enables downloading storage items using the client, instead of going through DagsHub's server.
    For custom clients use `enable_custom_bucket_downloader` function

    Args:
        client: a boto3 S3 client.
            If client isn't specified, the default parameterless constructor is used
    """

    if client is None:
        import boto3
        client = boto3.client("s3")

    def get_fn(bucket, path) -> bytes:
        resp = client.get_object(Bucket=bucket, Key=path)
        return resp["Body"].read()

    add_bucket_downloader("s3", get_fn)


def download_url_to_bucket_path(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Gets a storage download URL of a dagshub file, returns a tuple of (protocol, bucket, path_in_bucket)
    """
    matches = storage_download_url_regex.match(url)
    if matches is None:
        return None
    groups = matches.groupdict()
    return groups["proto"], groups["bucket"], groups["path"]


def _dagshub_download(url: str, auth: HTTPBearerAuth) -> bytes:
    resp = http_request("GET", url, auth=auth, timeout=600)
    try:
        assert resp.status_code == 200
    # TODO: retry
    except AssertionError:
        raise RuntimeError(
            f"Couldn't download file at URL {url}. Response code {resp.status_code} (Body: {resp.content})")
    return resp.content


BucketDownloaderFuncType = Callable[[str, str], bytes]

_bucket_downloader_map: Dict[str, BucketDownloaderFuncType] = {}
_default_downloader: Optional[Callable[[str], bytes]] = None


def add_bucket_downloader(proto: Literal["gs", "s3"], func: BucketDownloaderFuncType):
    if proto in _bucket_downloader_map:
        logger.warning(f"Protocol {proto} already has a custom downloader function specified, overwriting it")
    _bucket_downloader_map[proto] = func


def _download_wrapper(url: str, location: Path, skip_if_exists: bool):
    if skip_if_exists and os.path.exists(location):
        return

    # Download the file
    # Check if it's a bucket
    bucket_tuple = download_url_to_bucket_path(url)
    assert _default_downloader is not None
    if bucket_tuple is None:
        # Not a bucket path - download regularly
        content = _default_downloader(url)
    else:
        # Bucket path - try to look if there's a custom downloader
        proto, bucket_name, bucket_path = bucket_tuple
        bucket_downloader = _bucket_downloader_map.get(proto)
        if bucket_downloader is None:
            content = _default_downloader(url)
        else:
            content = bucket_downloader(bucket_name, bucket_path)

    location.parent.mkdir(parents=True, exist_ok=True)
    with open(location, "wb") as f:
        f.write(content)


def _ensure_default_downloader_exists():
    """
    Checks that the default dagshub download function exists and prepares it otherwise
    """
    global _default_downloader
    if _default_downloader is None:
        token = config.token or get_token(host=config.host)
        _default_downloader = partial(_dagshub_download, auth=HTTPBearerAuth(token=token))


def download_files(files: List[Tuple[str, Union[str, Path]]],
                   download_fn: Optional[DownloadFunctionType] = None,
                   threads=32, skip_if_exists=True):
    """
    Download files using multithreading

    Parameters:
        files: list of (download_url: str, file_location: str or Path)
        download_fn: Optional function that will download the file. Needs to receive the two arguments:
            download url and Path where to save the file
            If function is not specified, then a default function that downloads a file with DagsHub credentials is used
            CAUTION: function needs to be pickleable since we're using ThreadPool to execute
        threads: number of threads to run this function on, default 32
        skip_if_exists: skip the download if the file exists (only for the default downloader)
    """
    _ensure_default_downloader_exists()

    # Convert string paths to Path objects
    for i, file_tuple in enumerate(files):
        if type(file_tuple[1]) is str:
            files[i] = (file_tuple[0], Path(file_tuple[1]))

    if download_fn is None:
        download_fn = partial(_download_wrapper, skip_if_exists=skip_if_exists)

    if len(files) > 1:
        # Multiple files - multithreaded download
        progress = get_rich_progress(rich.progress.MofNCompleteColumn(), transient=False)
        task = progress.add_task("Downloading files...", total=len(files))

        with progress:
            with ThreadPoolExecutor(max_workers=threads) as tp:

                def cancel_download(*args):
                    logger.warning("Interrupt received - shutting down downloader")
                    tp.shutdown(wait=False, cancel_futures=True)

                orig_interrupt = None
                try:
                    orig_interrupt = signal.signal(signal.SIGINT, cancel_download)
                # ValueError means the function is not running from the main thread.
                # TODO: figure out a workaround
                except ValueError:
                    pass

                futures = [tp.submit(download_fn, url, location) for (url, location) in files]
                for f in as_completed(futures):
                    exc = f.exception()
                    if exc is not None:
                        logger.warning(f"Got exception {type(exc)} while downloading file: {exc}")
                    progress.update(task, advance=1)

                if orig_interrupt is not None:
                    signal.signal(signal.SIGINT, orig_interrupt)

    elif len(files) == 1:
        # Single file - don't bother with the multithreading, just download the file
        url, location = files[0]
        try:
            download_fn(url, location)
        except Exception as exc:
            logger.warning(f"Got exception {type(exc)} while downloading file: {exc}")
