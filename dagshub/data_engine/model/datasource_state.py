import logging
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath, Path
from typing import Optional, Union, Mapping, Any, Dict, List
from os import PathLike
from dagshub.common.api.repo import RepoAPI, PathNotFoundError
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.models import DatasourceType, DatasourceResult, PreprocessingStatus, MetadataFieldSchema
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.errors import DatasourceAlreadyExistsError, DatasourceNotFoundError
from dagshub.common.util import multi_urljoin

from functools import cached_property

logger = logging.getLogger(__name__)

path_regexes = {
    DatasourceType.BUCKET: re.compile(r"(?P<schema>s3|gs|azure)://(?P<bucket>[\w\-._]+)(?P<prefix>/.*)?"),
    DatasourceType.REPOSITORY: re.compile(r"repo://(?P<user>[\w\-_.]+)/(?P<repo>[\w\-_.]+)(?P<prefix>/.*)?"),
}

expected_formats = {
    DatasourceType.BUCKET: "s3|gs|azure://bucket-name/prefix",
    DatasourceType.REPOSITORY: "repo://owner/reponame/prefix",
}


class InvalidPathFormatError(Exception):
    pass


@dataclass
class DatasourceState:
    repo: str
    name: Optional[str] = field(default=None)
    id: Optional[Union[int, str]] = field(default=None)

    source_type: DatasourceType = field(init=False)
    preprocessing_status: PreprocessingStatus = field(init=False)
    path: str = field(init=False)
    client: DataClient = field(init=False)
    repoApi: RepoAPI = field(init=False)
    metadata_fields: List[MetadataFieldSchema] = field(init=False)

    _revision: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        self.client = DataClient(self.repo)
        self.repoApi = RepoAPI(self.repo)
        if hasattr(self, "source_type") and self.source_type == DatasourceType.REPOSITORY:
            self.revision = self.path_parts()["revision"]
        if not hasattr(self, "metadata_fields"):
            self.metadata_fields = []

    @property
    def revision(self) -> str:
        """Used for repository sources, provides branch/revision from which to download files"""
        if self._revision is None:
            logger.warning("Revision wasn't set, assuming default repo branch")
            self.revision = self.repoApi.default_branch
        return self._revision

    @property
    def url(self) -> str:
        return multi_urljoin(self.repoApi.repo_url, f"datasets/datasource/{self.id}/gallery")

    @revision.setter
    def revision(self, val: str):
        self._revision = val

    def create(self):
        # Check that a datasource with this name doesn't exist
        datasources = self.client.get_datasources(self.id, self.name)
        if len(datasources) != 0:
            raise DatasourceAlreadyExistsError(self)

        create_result = self.client.create_datasource(self)
        self._update_from_ds_result(create_result)

    def get_from_dagshub(self):
        sources = self.client.get_datasources(self.id, self.name)
        if len(sources) == 0:
            raise DatasourceNotFoundError(self)
        elif len(sources) > 1:
            raise RuntimeError(
                f"Got too many ({len(sources)}) datasources with name '{self.name}' or id. Something went wrong"
            )
        self._update_from_ds_result(sources[0])

    def content_path(self, path: Union[str, Datapoint, Mapping[str, Any]]) -> str:
        """
        Returns the url for the content path of a specified path
        """
        path = self._extract_path(path)
        return multi_urljoin(self.root_content_path, path)

    def raw_path(self, path: Union[str, Datapoint, Mapping[str, Any]]) -> str:
        """
        Returns the url for the download path of a specified path
        """
        path = self._extract_path(path)
        return multi_urljoin(self.root_raw_path, path)

    @property
    def source_prefix(self) -> PurePosixPath:
        parts = self.path_parts()
        if parts.get("prefix"):
            return PurePosixPath(parts["prefix"].strip("/"))
        else:
            return PurePosixPath()

    def file_path(self, path: Union[str, Datapoint, Mapping[str, Any]]) -> PurePosixPath:
        """
        Returns the generic path of the path in the repo (adds prefix)
        """
        return self.source_prefix / self._extract_path(path)

    def blob_path(self, sha: str) -> str:
        """
        Returns the path for the blob of a datasource
        """
        return f"{self.repoApi.data_engine_url}/blob/{sha}"

    @cached_property
    def root_content_path(self) -> str:
        """
        Returns the root content path of the dataset for listing folders
        This is just a "prefix" of the datasource relative to the repo.
        In order to build a path of an entity you need to concatenate the path to this root
        """
        return self._root_path("content")

    @cached_property
    def root_raw_path(self):
        """
        Returns the root raw path of the dataset for downloading files
        This is just a "prefix" of the datasource relative to the repo.
        In order to build a path of an entity you need to concatenate the path to this root
        """
        return self._root_path("raw")

    def _root_path(self, path_type):
        assert path_type in ["raw", "content"]
        parts = self.path_parts()
        if self.source_type == DatasourceType.BUCKET:
            path_elems = [parts["schema"], parts["bucket"]]
            if parts.get("prefix"):
                path_elems.append(parts["prefix"])
            path_prefix = "/".join(path_elems)
            if path_type == "raw":
                return self.repoApi.storage_raw_api_url(path_prefix)
            elif path_type == "content":
                return self.repoApi.storage_content_api_url(path_prefix)
        elif self.source_type == DatasourceType.REPOSITORY:
            prefix = parts["prefix"]
            if prefix is None:
                prefix = ""
            # Assuming repo://user/repo is always the same user/repo we work with
            if path_type == "raw":
                return self.repoApi.raw_api_url(prefix, self.revision)
            elif path_type == "content":
                return self.repoApi.content_api_url(prefix, self.revision)
        elif self.source_type == DatasourceType.CUSTOM:
            raise NotImplementedError
        raise NotImplementedError

    def path_parts(self) -> Dict[str, str]:
        """
        Validates the provided path + returns a dictionary with elements that might be relevant for constructing paths
        """
        regex = path_regexes[self.source_type]
        match = regex.fullmatch(self.path)
        if match is None:
            raise InvalidPathFormatError(
                f"{self.path} is not valid path format for type {self.source_type}.\n"
                f"Expected format: {expected_formats[self.source_type]}"
            )
        res = match.groupdict()
        # For repository type - handle revision that is in format of repo://user/repo/branch:prefix
        # Couldn't do that with regexes, so handling it here
        if self.source_type == DatasourceType.REPOSITORY:
            res["revision"] = None
            if res.get("prefix"):
                prefix = res["prefix"]
                if ":" in prefix:
                    revision, prefix = prefix.split(":", 1)
                    res["revision"] = revision.strip("/")
                    if prefix.isspace():
                        prefix = None
                    elif not prefix.startswith("/"):
                        prefix = "/" + prefix
                    res["prefix"] = prefix
        return res

    @staticmethod
    def _extract_path(val: Union[str, Datapoint, Mapping[str, Any]]) -> str:
        if type(val) is str:
            return val
        elif type(val) is Datapoint:
            return val.path
        return val["path"]

    def _update_from_ds_result(self, ds: DatasourceResult):
        self.id = ds.id
        self.name = ds.name
        self.path = ds.rootUrl
        self.source_type = ds.type
        self.preprocessing_status = ds.preprocessingStatus
        self.metadata_fields = [] if ds.metadataFields is None else ds.metadataFields
        if self.source_type == DatasourceType.REPOSITORY:
            self.revision = self.path_parts()["revision"]

    @staticmethod
    def from_gql_result(repo: str, res: DatasourceResult):
        ds = DatasourceState(repo)
        ds._update_from_ds_result(res)
        return ds

    def import_metadata_from_file(self, datasource_name: str, file_path: Union[str, PathLike], path_column: str):
        load_location = self._determine_load_location(file_path)
        file_name = Path(file_path).name
        file_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        file_bytes = None
        if load_location == "disk":
            file_bytes = open(file_path, "rb")
        elif load_location == "repo":
            file_bytes = self.repoApi.get_file(file_path)

        files = {
            "file": (file_name, file_bytes, file_type),
        }
        data = {
            "datasource_name": datasource_name,
            "path_column": path_column,
        }

        url = multi_urljoin(self.repoApi.data_engine_url, "import/metadata")
        res = self.repoApi._http_request("POST", url, data=data, files=files)
        if res.status_code == 404:
            raise PathNotFoundError(f"Datasource {datasource_name} not found")
        elif res.status_code >= 400:
            error_msg = f"Got status code {res.status_code} when importing metadata to datasource {datasource_name}"
            logger.error(error_msg)
            logger.debug(res.content)
            raise RuntimeError(error_msg)
        return res.content

    def _determine_load_location(self, file_path: Union[str, Path]) -> str:
        # Local files take priority
        if Path(file_path).exists():
            return "disk"

        # Try to find it in the repo otherwise
        try:
            files = self.repoApi.list_path(Path(file_path).as_posix())
            if len(files) > 0:
                return "repo"
        except PathNotFoundError:
            pass

        # TODO: handle repo bucket too
        # TODO: improve and reuse https://github.com/DagsHub/client/pull/517#issuecomment-2288690281

        raise PathNotFoundError(f"Path {file_path} not found")
