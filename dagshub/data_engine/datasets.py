import json
from typing import List, Optional, Union

from dagshub.common.analytics import send_analytics_event
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.models import DatasetResult
from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.model.datasource_state import DatasourceState
from dagshub.data_engine.model.errors import DatasetNotFoundError
from dagshub.data_engine.model.query import DatasourceQuery


def get_datasets(repo: str) -> List[Datasource]:
    """
    Gets datasets assigned to the repo.
    Dataset is a combination of a datasource with a query + include/exclude lists
    """
    return _get_datasets(repo)


def get_dataset(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None) -> Datasource:
    """
    Get specific dataset (by name or id)
    """
    assert name is not None or id is not None

    sources = _get_datasets(repo, name, id)
    if len(sources) == 0:
        raise DatasetNotFoundError(repo, id, name)
    return sources[-1]


def _get_datasets(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None) -> List[Datasource]:
    send_analytics_event("Client_DataEngine_getDatasets")
    client = DataClient(repo)
    sources = client.get_datasets(id, name)
    return [_from_gql_result(repo, source) for source in sources]


def _from_gql_result(repo: str, dataset_result: "DatasetResult") -> "Datasource":
    ds = Datasource(DatasourceState.from_gql_result(repo, dataset_result.datasource))

    query_dict = json.loads(dataset_result.datasetQuery)
    if "query" in query_dict:
        ds._query = DatasourceQuery.deserialize(query_dict["query"])

    return ds
