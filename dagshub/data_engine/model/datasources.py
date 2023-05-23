import logging
from typing import Optional, Union, List

from dagshub.data_engine.client.data_client import DataClient
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
    source = _create_datasource_state(repo, name, DataSourceType.REPOSITORY, url)
    source.revision = revision
    return DataSource(source)


def create_from_dataset(repo: str, name: str, dataset_name: str) -> DataSource:
    source = _create_datasource_state(repo, name, DataSourceType.CUSTOM, dataset_name)
    return DataSource(source)


def get_datasource(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None, **kwargs) -> DataSource:
    """
    Additional kwargs:
    revision - for repo datasources defines which branch/revision to download from (default branch if not specified)
    """
    ds_state = DataSourceState(repo=repo, name=name, id=id)
    ds_state.get_from_dagshub()
    if "revision" in kwargs:
        ds_state.revision = kwargs["revision"]
    return DataSource(ds_state)


def get_datasources(repo: str) -> List[DataSource]:
    client = DataClient(repo)
    sources = client.get_datasources(None, None)
    return [DataSource(DataSourceState.from_gql_result(repo, source)) for source in sources]


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
