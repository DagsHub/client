from typing import List, Optional, Union

from dagshub.common.analytics import send_analytics_event
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.models import DatasetResult
from dagshub.data_engine import datasources
from dagshub.data_engine.model.datasource import Datasource, DEFAULT_MLFLOW_ARTIFACT_NAME, DatasetState
from dagshub.data_engine.model.datasource_state import DatasourceState
from dagshub.data_engine.model.errors import DatasetNotFoundError


def get_datasets(repo: str) -> List[Datasource]:
    """
    Get all datasources that exist on the repo

    Args:
        repo: Repo in ``<owner>/<reponame>`` format

    Returns:
        list(Datasource): All datasets of the repo
    """
    return _get_datasets(repo)


def get_dataset(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None) -> Datasource:
    """
    Get specific dataset by name or id

    Args:
        repo: Repo in ``<owner>/<reponame>`` format
        name: Name of the dataset
        id: ID of the dataset

    Returns:
        Datasource: Found dataset

    Raises:
        DatasetNotFoundError: No dataset found with this name or id
    """
    assert name is not None or id is not None

    sources = _get_datasets(repo, name, id)
    if len(sources) == 0:
        raise DatasetNotFoundError(repo, id, name)
    return sources[-1]


def get_dataset_from_file(path: str) -> Datasource:
    """
    Load a dataset from a local file.

    This is a copy of
    :func:`datasources.get_datasource_from_file()<dagshub.data_engine.datasources.get_datasource_from_file>`

    Args:
        path: Path to the ``.dagshub`` file with the relevant dataset

    Returns:
        dataset that was logged to the file
    """
    return datasources.get_datasource_from_file(path)


def get_from_mlflow(run=None, artifact_name=DEFAULT_MLFLOW_ARTIFACT_NAME) -> Datasource:
    """
    Load a dataset from an MLflow run.

    To save a datasource to MLflow, use
    :func:`Datasource.log_to_mlflow()<dagshub.data_engine.model.datasource.Datasource.log_to_mlflow>`.

    This is a copy of :func:`datasources.get_from_mlflow()<dagshub.data_engine.datasources.get_from_mlflow>`

    Args:
        run: Run or ID of the MLflow run to load the datasource from.
            If ``None``, gets it from the current active run.
        artifact_name: Name of the artifact in the run.
    """
    return datasources.get_from_mlflow(run, artifact_name)


def _get_datasets(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None) -> List[Datasource]:
    send_analytics_event("Client_DataEngine_getDatasets")
    client = DataClient(repo)
    sources = client.get_datasets(id, name)
    return [_from_gql_result(repo, source) for source in sources]


def _from_gql_result(repo: str, dataset_result: "DatasetResult") -> "Datasource":
    ds = Datasource(DatasourceState.from_gql_result(repo, dataset_result.datasource))

    dataset_state = DatasetState.from_gql_dataset_result(dataset_result)
    ds.load_from_dataset_state(dataset_state)
    return ds
