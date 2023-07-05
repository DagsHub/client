from typing import Literal

from dagshub.common.download import BucketDownloaderFuncType, add_bucket_downloader


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

    enable_custom_bucket_downloader("gcs", get_fn)


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

    enable_custom_bucket_downloader("s3", get_fn)


def enable_custom_bucket_downloader(protocol: Literal["gcs", "s3"], download_func: BucketDownloaderFuncType):
    """
    Enables downloading storage items using a custom function
    The function must receive two arguments: bucket name and a path, returns the binary content of the downloaded file

    Args:
        download_func: Function that receives a tuple of (protocol, bucket_name, path_in_bucket)
            and returns the IOBase of the bytes
        protocol: Which protocol the bucket is, possible values are gcs or s3
    """

    add_bucket_downloader(protocol, download_func)
