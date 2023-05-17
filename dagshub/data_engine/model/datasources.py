import logging
from typing import Optional, Union

from dagshub.data_engine.client.dataclasses import DataSourceType
from dagshub.data_engine.model.datasource import DataSource
from dagshub.data_engine.model.datasource_state import DataSourceState

logger = logging.getLogger(__name__)


def create_from_bucket(repo: str, name: str, bucket_url: str) -> DataSource:
    # TODO: validation
    source = _create_datasource_state(repo, name, DataSourceType.BUCKET, bucket_url)
    return DataSource(source)


def create_from_repo(repo: str, name: str, path: str, revision: str = "main") -> DataSource:
    url = f"repo://{repo}/{path}"
    # TODO: figure out what to do with the revision
    source = _create_datasource_state(repo, name, DataSourceType.REPOSITORY, url)
    return DataSource(source)


def create_from_dataset(repo: str, name: str, dataset_name: str) -> DataSource:
    source = _create_datasource_state(repo, name, DataSourceType.CUSTOM, dataset_name)
    return DataSource(source)


def get_datasource(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None) -> DataSource:
    ds = DataSourceState(repo=repo, name=name, id=id)
    ds.get_from_dagshub()
    return DataSource(ds)


def _create_datasource_state(repo: str, name: str, source_type: DataSourceType, path: str) -> DataSourceState:
    ds = DataSourceState(name=name, repo=repo)
    ds.source_type = source_type
    ds.path = path
    ds.create()
    return ds


__all__ = [
    create_from_bucket,
    create_from_repo,
    create_from_dataset,
    get_datasource,
]
