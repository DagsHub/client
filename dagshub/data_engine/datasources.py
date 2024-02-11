import json
import logging
from typing import Optional, Union, List, TYPE_CHECKING

from dagshub.common.analytics import send_analytics_event
from dagshub.common.api.repo import RepoAPI
from dagshub.common.util import lazy_load
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.model.datasource import Datasource, DEFAULT_MLFLOW_ARTIFACT_NAME
from dagshub.data_engine.model.datasource_state import DatasourceState, DatasourceType, path_regexes
from dagshub.data_engine.model.errors import DatasourceNotFoundError

if TYPE_CHECKING:
    import mlflow
    import mlflow.artifacts as mlflow_artifacts
    import mlflow.entities
else:
    mlflow = lazy_load("mlflow")
    mlflow_artifacts = lazy_load("mlflow.artifacts", "mlflow")

logger = logging.getLogger(__name__)


def create_datasource(repo: str, name: str, path: str, revision: Optional[str] = None) -> Datasource:
    """
    Create a datasource from a path in the repo or a storage bucket URL.
    You can have multiple datasources pointing at the same path.

    Args:
        repo: Repo in ``<owner>/<reponame>`` format
        name: Name of the datasource to be created. Name should be unique across the repository's datasources
        path: Either of:

            - a path to a directory inside the Git/DVC repo on DagsHub:
                ``path/to/dir``
            - URL pointing to a storage bucket which is connected to the DagsHub repo:
                ``s3://bucketname/path/in/bucket``
        revision: Branch or revision the datasource should be used with.
                    Only valid when using a Git/DVC path inside the DagsHub repo.
                    The default repo branch is used if this is left blank.

    Returns:
        Datasource: Created datasource

    Raises:
        DatasourceAlreadyExistsError: Datasource with this name already exists in repo.

    """

    if path_regexes[DatasourceType.BUCKET].fullmatch(path):
        if revision is not None:
            raise ValueError("revision cannot be used together with bucket URLs")
        return create_from_bucket(repo, name, bucket_url=path)
    else:
        return create_from_repo(repo, name, path=path, revision=revision)


def create(*args, **kwargs) -> Datasource:
    """Alias for :func:`create_datasource`"""
    return create_datasource(*args, **kwargs)


def get_or_create(repo: str, name: str, path: str, revision: Optional[str] = None) -> Datasource:
    """
    First attempts to get the repo datasource with the given name, and only if that fails,
    invokes create_datasource with the given parameters.
    See the docs on create_datasource for more info.



    Args:
        repo (str): Repo in the format of `user/repo`
        name (str): The name of the datasource to retrieve or create.
        path (str): The path to the datasource within the repository.
        revision (Optional[str], optional): The specific revision or version of the datasource to retrieve.

    Returns:
        Datasource: The retrieved or newly created Datasource instance.

    Raises:
        DatasourceAlreadyExistsError: Datasource with this name already exists in repo.
    """
    try:
        return get_datasource(repo, name)
    except DatasourceNotFoundError:
        return create_datasource(repo, name, path, revision)


def create_from_bucket(repo: str, name: str, bucket_url: str) -> Datasource:
    """
    :meta private:
    """
    # TODO: validation
    source = _create_datasource_state(repo, name, DatasourceType.BUCKET, bucket_url)
    return Datasource(source)


def create_from_repo(repo: str, name: str, path: str, revision: Optional[str] = None) -> Datasource:
    """
    :meta private:
    """
    if revision is None:
        repo_api = RepoAPI(repo)
        revision = repo_api.default_branch
    url = f"repo://{repo}/{revision}:{path.lstrip('/')}"
    source = _create_datasource_state(repo, name, DatasourceType.REPOSITORY, url)
    if revision is not None:
        source.revision = revision
    return Datasource(source)


def get_datasource(repo: str, name: Optional[str] = None, id: Optional[Union[int, str]] = None, **kwargs) -> Datasource:
    """
    Gets datasource with matching name or id for the repo

    Args:
        repo: Repo in ``<owner>/<reponame>`` format
        name: Name of the datasource
        id: ID of the datasource

    Kwargs:
        revision - for repo datasources defines which branch/revision to download from.
        If not specified, uses the default branch of the repo

    Returns:
        Datasource: datasource that has supplied name and/or id

    Raises:
        DatasourceNotFoundError: The datasource with this id or name does not exist.

    """
    ds_state = DatasourceState(repo=repo, name=name, id=id)
    ds_state.get_from_dagshub()
    if "revision" in kwargs:
        ds_state.revision = kwargs["revision"]
    return Datasource(ds_state)


def get_datasource_from_file(path: str) -> Datasource:
    """
    [EXPERIMENTAL]
    Load a datasource from a local file

    Args:
        path: Path to the ``.dagshub`` file with the relevant datasource

    Returns:
        ds: Datasource that was logged to the file
    """
    with open(path, "r") as file:
        state = json.load(file)
    return Datasource.load_from_serialized_state(state)


def get_datasources(repo: str) -> List[Datasource]:
    """
    Get all datasources that exist on the repo

    Args:
        repo: Repo in ``<owner>/<reponame>`` format

    Returns:
        list(Datasource): All datasources that exist for the repository
    """
    send_analytics_event("Client_DataEngine_getDatasources")
    client = DataClient(repo)
    sources = client.get_datasources(None, None)
    return [Datasource(DatasourceState.from_gql_result(repo, source)) for source in sources]


def get_from_mlflow(
    run: Optional[Union["mlflow.entities.Run", str]] = None, artifact_name=DEFAULT_MLFLOW_ARTIFACT_NAME
) -> Datasource:
    """
    Load a datasource from an MLflow run.

    To save a datasource to MLflow, use
    :func:`Datasource.log_to_mlflow()<dagshub.data_engine.model.datasource.Datasource.log_to_mlflow>`.

    Args:
        run: MLflow Run or its ID to load the datasource from.
            If ``None``, loads datasource from the current active run.
        artifact_name: Name of the datasource artifact in the run.
    """
    mlflow_run: "mlflow.entities.Run"
    if run is None:
        mlflow_run = mlflow.active_run()
    elif type(run) is str:
        mlflow_run = mlflow.get_run(run)
    else:
        mlflow_run = run

    artifact_uri: str = mlflow_run.info.artifact_uri
    artifact_path = f"{artifact_uri.rstrip('/')}/{artifact_name.lstrip('/')}"

    ds_state = mlflow_artifacts.load_dict(artifact_path)
    return Datasource.load_from_serialized_state(ds_state)


def get(*args, **kwargs) -> Datasource:
    """Alias for :func:`get_datasource`"""
    return get_datasource(*args, **kwargs)


def _create_datasource_state(repo: str, name: str, source_type: DatasourceType, path: str) -> DatasourceState:
    ds = DatasourceState(name=name, repo=repo)
    ds.source_type = source_type
    ds.path = path
    ds.create()
    return ds


__all__ = [
    create_datasource.__name__,
    create.__name__,
    create_from_bucket.__name__,
    create_from_repo.__name__,
    get_datasource.__name__,
    get_datasources.__name__,
    get.__name__,
    get_or_create.__name__,
    get_from_mlflow.__name__,
]
