import logging
import os
from dataclasses import dataclass
from enum import auto, IntEnum
from functools import cached_property
from pathlib import Path, PurePosixPath
from typing import Optional, Literal, Union, Tuple, List

import dacite
import yaml
from pathvalidate import sanitize_filepath

from dagshub.common.analytics import send_analytics_event
from dagshub.common.api import RepoAPI
from dagshub.common.api.repo import PathNotFoundError
from dagshub.common.api.responses import StorageAPIEntry
from dagshub.common.determine_repo import determine_repo
from dagshub.common.helpers import log_message
from dagshub.models.model_loaders import (
    ModelLoader,
    RepoModelLoader,
    BucketModelLoader,
    DagsHubStorageModelLoader,
)

# TODO: don't forget to separate dvc downloads by the hash of the dir

logger = logging.getLogger(__name__)


class ModelNotFoundError(Exception):
    def __str__(self):
        return "Could not find model"


@dataclass
class ModelYamlStruct:
    model_dir: str


class StorageType(IntEnum):
    Repo = auto()
    DagshubStorage = auto()
    Bucket = auto()


class ModelLocator:
    def __init__(
        self,
        repo: Optional[Union[str, RepoAPI]] = None,
        path: Optional[str] = None,
        bucket: Optional[str] = None,
        git_ref: Optional[str] = None,
        mlflow_model: Optional[str] = None,
        mlflow_artifact: Optional[str] = None,
        download_dest: Optional[Union[str, os.PathLike]] = None,
        download_type: Literal["lazy", "eager"] = "eager",
    ):
        self._repo = repo
        self.path = path
        self.bucket = bucket
        self._git_ref = git_ref
        self.mlflow_model = mlflow_model
        self.mlflow_artifact = mlflow_artifact
        self._download_dest = download_dest
        self.download_type = download_type

    @cached_property
    def repo_api(self) -> RepoAPI:
        if isinstance(self._repo, RepoAPI):
            return self._repo
        if self._repo is None:
            repo_api, git_ref = determine_repo()
            if self._git_ref is None:
                self._git_ref = git_ref
            return repo_api
        return RepoAPI(self._repo)

    @property
    def git_ref(self):
        if self._git_ref is None:
            self._git_ref = self.repo_api.default_branch
        return self._git_ref

    @cached_property
    def download_destination(self) -> Path:
        if self._download_dest is not None:
            return Path(self._download_dest)
        return Path(
            sanitize_filepath(
                os.path.join(Path.home(), "dagshub", "models", self.repo_api.full_name)
            )
        )

    @cached_property
    def repo_storages(self) -> List[StorageAPIEntry]:
        return self.repo_api.get_connected_storages()

    def _handle_path(self, path: str) -> Tuple[str, StorageType]:
        """
        Handles user-printed path.
        Returns a resulting path that can be queried from DagsHub + boolean for whether it's a repo or a bucket path
        If path is a repo path, returns (path as is, StorageType.Repo)
        If path is a storage path, ({actual path in storage} + StorageType.Bucket/DagshubStorage)
        Storage path resolution is based on bucket name, if the path starts with a name of an existing bucket,
        assume that it's a storage path
        """
        str_path = str(path)

        if "/" not in str_path:
            return path, StorageType.Repo

        if str_path.startswith("dagshub_storage/"):
            return str_path[len("dagshub_storage/") :], StorageType.DagshubStorage
        for storage in self.repo_storages:
            if str_path.startswith(f"{storage.name}/"):
                bucketPath = f"{storage.protocol}/{str_path}"
                return bucketPath, StorageType.Bucket
        return path, StorageType.Repo

    def try_load_yaml(self, yaml_path=".dagshub/model.yaml") -> Optional[ModelLoader]:
        """
        Loads the info about where the model stored from a .yaml file
        """
        try:
            yaml_contents = self.repo_api.get_file(yaml_path)
        except PathNotFoundError:
            return None
        cfg = dacite.from_dict(ModelYamlStruct, yaml.safe_load(yaml_contents))

        model_path, storage_type = self._handle_path(cfg.model_dir)
        log_message(f"Loading the model from yaml file {yaml_path}", logger=logger)
        if storage_type == StorageType.DagshubStorage:
            try:
                self.repo_api.list_storage_path(
                    f"s3/{self.repo_api.repo_name}/{model_path}"
                )
                log_message(
                    f"Loading the model from DagsHub Storage {model_path}",
                    logger=logger,
                )
                return DagsHubStorageModelLoader(
                    self.repo_api, PurePosixPath(model_path)
                )
            except PathNotFoundError:
                raise ModelNotFoundError
        elif storage_type == StorageType.Bucket:
            try:
                self.repo_api.list_storage_path(model_path)
                log_message(
                    f"Loading the model from bucket {model_path}", logger=logger
                )
                return BucketModelLoader(self.repo_api, PurePosixPath(model_path))
            except PathNotFoundError:
                raise ModelNotFoundError
        else:
            try:
                self.repo_api.list_path(model_path, revision=self.git_ref)
                log_message(f"Loading the model from repo {model_path}", logger=logger)
                return RepoModelLoader(
                    self.repo_api, self.git_ref, PurePosixPath(model_path)
                )
            except PathNotFoundError:
                raise ModelNotFoundError

    lookup_dirs = ["model", "models"]

    def try_find_model_in_repo(self) -> Optional[ModelLoader]:
        for lookup_dir in self.lookup_dirs:
            modelPath = PurePosixPath(lookup_dir)
            try:
                self.repo_api.list_path(str(modelPath), revision=self.git_ref)
                log_message(
                    f"Loading the model from repo directory {modelPath}", logger=logger
                )
                return RepoModelLoader(
                    repo_api=self.repo_api, revision=self.git_ref, path=modelPath
                )
            except PathNotFoundError:
                continue
        return None

    def try_find_model_in_bucket(self, bucket: str) -> Optional[ModelLoader]:
        bucketPath: Optional[PurePosixPath] = None
        for storage in self.repo_storages:
            if storage.name.startswith(bucket):
                bucketPath = PurePosixPath(f"{storage.protocol}/{storage.name}")
                break

        if bucketPath is None:
            return None

        for lookup_dir in self.lookup_dirs:
            modelPath = bucketPath / lookup_dir
            try:
                self.repo_api.list_storage_path(str(modelPath))
                log_message(
                    f"Loading the model from bucket directory {modelPath}",
                    logger=logger,
                )
                return BucketModelLoader(repo_api=self.repo_api, path=modelPath)
            except PathNotFoundError:
                continue

        return None

    def try_find_model_in_dagshub_storage(self) -> Optional[ModelLoader]:
        bucketPath = PurePosixPath("s3") / self.repo_api.repo_name
        for modelPath in self.lookup_dirs:
            try:
                self.repo_api.list_storage_path(str(bucketPath / modelPath))
                log_message(
                    f"Loading the model from DagsHub Storage directory {modelPath}",
                    logger=logger,
                )
                return DagsHubStorageModelLoader(
                    repo_api=self.repo_api, path=PurePosixPath(modelPath)
                )
            except PathNotFoundError:
                continue

        return None

    def find_model(self) -> ModelLoader:
        model_loader: Optional[ModelLoader]

        if self.path is not None:
            # Check that the dir exists and return that
            handled_path, storage_type = self._handle_path(self.path)
            try:
                if storage_type == storage_type.Bucket:
                    self.repo_api.list_storage_path(handled_path)
                    return BucketModelLoader(self.repo_api, PurePosixPath(handled_path))
                elif storage_type == storage_type.DagshubStorage:
                    self.repo_api.list_storage_path(
                        PurePosixPath("s3") / self.repo_api.repo_name / handled_path
                    )
                    return DagsHubStorageModelLoader(
                        self.repo_api, PurePosixPath(handled_path)
                    )
                else:
                    self.repo_api.list_path(handled_path, self.git_ref)
                    return RepoModelLoader(
                        self.repo_api, self.git_ref, PurePosixPath(handled_path)
                    )
            except PathNotFoundError:
                raise ModelNotFoundError

        if self.bucket is not None:
            model_loader = self.try_find_model_in_bucket(self.bucket)
            if model_loader is None:
                raise ModelNotFoundError
            if model_loader is not None:
                return model_loader

        # TODO: add mlflow here

        model_loader = self.try_load_yaml()
        if model_loader is not None:
            return model_loader

        model_loader = self.try_find_model_in_repo()
        if model_loader is not None:
            return model_loader

        model_loader = self.try_find_model_in_dagshub_storage()
        if model_loader is not None:
            return model_loader

        raise ModelNotFoundError

    def get_model_path(self) -> Path:
        send_analytics_event("Client_Models_GetModelPath")
        model_loader = self.find_model()
        return model_loader.load_model(
            self.download_type, self.download_destination, self.git_ref
        )


def get_model_path(
    repo: Optional[str] = None,
    path: Optional[str] = None,
    bucket: Optional[str] = None,
    git_ref: Optional[str] = None,
    # mlflow_model: Optional[str] = None,
    # mlflow_artifact: Optional[str] = None,
    download_dest: Optional[Union[str, os.PathLike]] = None,
    download_type: Literal["lazy", "eager"] = "eager",
) -> Path:
    """
    Load a model path from a DagsHub repository in way that is compatible with the Hugging Face Transformers library.

    Example usage:

    .. code-block:: python

       from transformers import AutoModel
       from dagshub.models import get_model_path

       model = AutoModel.from_pretrained(get_model_path("<user_name>/<repo_name>"))

    The function looks for the model in following places in the repository, in this order:

    - **.dagshub/model.yaml** file in the repository. The file format should be::

        model_dir: <path_to_model_dir_in_repo>

    - **model** and **models** dvc/git directories in the root of the repository
    - **model** and **models** directories in repository's DagsHub Storage

    If either ``path`` or ``bucket`` argument is specified, this lookup gets ignored.

    After a model has been found, it is either downloaded or mounted to a local directory,
    and the path to the directory with the model files is returned.

    Args:
        repo: Name of the repository to load the model from in the format of ``<user>/<repo>``. \
        If ``None`` tries to get a DagsHub repository from a git repository in the current working directory
        path: Path to the directory with the model in the repository. This skips the model resolution step.
        bucket: Name of the bucket with the model. If specified, the model will be loaded from either \
        ``<bucket>/model`` or ``<bucket>/models`` directories. This skips the model resolution step.
        git_ref: Specific git revision/branch to load model from. This only works for models versioned with dvc.
        download_dest: Path to the directory where to download the model. If ``None``, the model will be downloaded to \
        ``~/dagshub/models/<user>/<repo>/<path_to_model_in_repo>``. If specified, the model will be downloaded to \
        ``<download_dest>/<path_to_model_in_repo>``
        download_type: How to load the models. Possible values:

            - ``lazy``: Mounts a streaming filesystem with :func:`install_hooks() <dagshub.streaming.install_hooks>` \
            that will download files on demand.
            - ``eager``: Downloads the whole model directory at once. Faster for models with a lot of files.

    .. warning::
        In order for download to work consistently between eager and lazy loading, the resulting path to the model \
        is always included in the returned path.

    .. note::
        If using .dagshub/model.yaml file or a path argument, and you want to use a bucket, specify:

        - ``dagshub_storage/<path_to_model_dir>`` to point to a folder in DagsHub Storage
        - ``<bucket_name>/<path_to_model_dir>`` if using an integrated bucket. For ``s3://my-bucket``,\
         the bucket name is ``my-bucket``

    Returns:
        Path to the directory with the models.
    """
    loader = ModelLocator(
        repo=repo,
        path=path,
        bucket=bucket,
        git_ref=git_ref,
        # mlflow_model=mlflow_model,
        # mlflow_artifact=mlflow_artifact,
        download_dest=download_dest,
        download_type=download_type,
    )
    return loader.get_model_path()
