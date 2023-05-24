import logging
from typing import Optional, Union, List

from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.dataclasses import DatasourceType
from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.model.datasource_state import DatasourceState

logger = logging.getLogger(__name__)


def create_from_bucket(repo: str, name: str, bucket_url: str) -> Datasource:
    # TODO: validation
    source = _create_datasource_state(repo, name, DatasourceType.BUCKET, bucket_url)
    return Datasource(source)


def create_from_repo(repo: str, name: str, path: str, revision: Optional[str] = None) -> Datasource:
    url = f"repo://{repo}/{path.lstrip('/')}"
    source = _create_datasource_state(repo, name, DatasourceType.REPOSITORY, url)
    if revision is not None:
        source.revision = revision
    return Datasource(source)


def create_from_dataset(repo: str, name: str, dataset_name: str) -> Datasource:
    source = _create_datasource_state(repo, name, DatasourceType.CUSTOM, dataset_name)
    return Datasource(source)


def get_datasource(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None, **kwargs) -> Datasource:
    """
    Additional kwargs:
    revision - for repo datasources defines which branch/revision to download from (default branch if not specified)
    """
    ds_state = DatasourceState(repo=repo, name=name, id=id)
    ds_state.get_from_dagshub()
    if "revision" in kwargs:
        ds_state.revision = kwargs["revision"]
    return Datasource(ds_state)


def get_datasources(repo: str) -> List[Datasource]:
    client = DataClient(repo)
    sources = client.get_datasources(None, None)
    return [Datasource(DatasourceState.from_gql_result(repo, source)) for source in sources]


def _create_datasource_state(repo: str, name: str, source_type: DatasourceType, path: str) -> DatasourceState:
    ds = DatasourceState(name=name, repo=repo)
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
