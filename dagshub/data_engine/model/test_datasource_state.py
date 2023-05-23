from dagshub.data_engine.client.dataclasses import DataSourceType
from dagshub.data_engine.model.datasource_state import path_regexes, DataSourceState, InvalidPathFormatError
import pytest


@pytest.mark.parametrize(
    "in_str, user, repo, prefix",
    [
        ("repo://user/repo/prefix", "user", "repo", "/prefix"),
        ("repo://user/repo/longer/prefix", "user", "repo", "/longer/prefix"),
        ("repo://user/repo/", "user", "repo", "/"),
        ("repo://user/repo", "user", "repo", None),
        ("repo://user-with_dashes/repo", "user-with_dashes", "repo", None),
        ("repo://user/repo-with_dashes", "user", "repo-with_dashes", None),
    ]
)
def test_repo_regex(in_str, user, repo, prefix):
    ds = DataSourceState(repo="user/repo")
    ds.path = in_str
    ds.source_type = DataSourceType.REPOSITORY
    res = ds.path_parts()

    expected = {
        "user": user,
        "repo": repo,
        "prefix": prefix
    }
    assert res == expected


@pytest.mark.parametrize(
    "in_str",
    [
        "s3://user/repo/prefix",
        "user/repo/",
        "repo://user.www.com/repo",
        "repo://user/",
        "repo://"
    ]
)
def test_repo_regex_incorrect(in_str):
    ds = DataSourceState(repo="user/repo")
    ds.path = in_str
    ds.source_type = DataSourceType.REPOSITORY
    with pytest.raises(InvalidPathFormatError):
        ds.path_parts()


@pytest.mark.parametrize(
    "in_str, schema, bucket, prefix",
    [
        ("s3://bucket/prefix", "s3", "bucket", "/prefix"),
        ("s3://bucket-name/prefix", "s3", "bucket-name", "/prefix"),
        ("s3://bucket/", "s3", "bucket", "/"),
        ("s3://bucket", "s3", "bucket", None),
        ("gs://bucket/prefix", "gs", "bucket", "/prefix"),
        ("s3://bucket/longer/prefix", "s3", "bucket", "/longer/prefix"),
    ]
)
def test_bucket_regex(in_str, schema, bucket, prefix):
    ds = DataSourceState(repo="user/repo")
    ds.path = in_str
    ds.source_type = DataSourceType.BUCKET
    res = ds.path_parts()

    expected = {
        "schema": schema,
        "bucket": bucket,
        "prefix": prefix
    }
    assert res == expected


@pytest.mark.parametrize(
    "in_str",
    [
        "notreallys3://bucket/prefix",
        "s3://",
        "s3://bucket.www.com/prefix",
    ]
)
def test_bucket_regex_incorrect(in_str):
    ds = DataSourceState(repo="user/repo")
    ds.path = in_str
    ds.source_type = DataSourceType.REPOSITORY
    with pytest.raises(InvalidPathFormatError):
        ds.path_parts()
