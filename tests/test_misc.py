import pytest

from dagshub.common.download import download_url_to_bucket_path


@pytest.mark.parametrize(
    "in_url, expected",
    [
        (
            "https://dagshub.com/api/v1/repos/kirill/bucket-repo/storage/raw/s3/dagshub-storage/images/047.png",
            ("s3", "dagshub-storage", "images/047.png"),
        )
    ],
)
def test_bucket_downloader_path_extraction(in_url, expected):
    actual = download_url_to_bucket_path(in_url)
    assert actual == expected


@pytest.mark.parametrize(
    "in_url", ["https://dagshub.com/api/v1/repos/kirill/bucket-repo/raw/main/images/047.png", "https://google.com"]
)
def test_bucket_download_path_extraction_fail(in_url):
    actual = download_url_to_bucket_path(in_url)
    assert actual is None
