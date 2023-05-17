import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Union, Mapping, Any

from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.dataclasses import DataSourceType, DataPoint, DataSourceResult
from dagshub.data_engine.model.errors import DatasourceAlreadyExistsError, DatasourceNotFoundError


@dataclass
class DataSourceState:
    repo: str
    name: Optional[str] = field(default=None)
    id: Optional[Union[int, str]] = field(default=None)

    source_type: DataSourceType = field(init=False)
    path: str = field(init=False)
    client: DataClient = field(init=False)

    def __post_init__(self):
        self.client = DataClient(self.repo)

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
                f"Got too many ({len(sources)}) datasources with name '{self.name}' or id. Something went wrong")
        self._update_from_ds_result(sources[0])

    def content_path(self, path: Union[str, DataPoint, Mapping[str, Any]]) -> str:
        return self._dagshub_api_path("content", self._extract_path(path))

    def raw_path(self, path: str) -> str:
        return self._dagshub_api_path("raw", self._extract_path(path))

    @staticmethod
    def _extract_path(val: Union[str, DataPoint, Mapping[str, Any]]) -> str:
        if type(val) is str:
            return val
        elif type(val) is DataPoint:
            return val.path
        return val["path"]

    def _dagshub_api_path(self, api_type: str, path: str) -> str:
        if self.source_type == DataSourceType.BUCKET:
            parsed_path = urllib.parse.urlparse(self.path)
            return f"{self.client.host}/api/v1/repos/{self.repo}/storage/{api_type}/{parsed_path.scheme}/" \
                   f"{parsed_path.hostname}/{parsed_path.path}/{path}"
        elif self.source_type == DataSourceType.REPOSITORY:
            # Assuming path format is "branch:/repo/path"
            branch, repo_path = self.path.split(":")
            return f"{self.client.host}/api/v1/repos/{self.repo}/{api_type}/{branch}/{repo_path}/{path}"
        raise NotImplementedError

    def _update_from_ds_result(self, ds: DataSourceResult):
        self.id = ds.id
        self.name = ds.name
        self.path = ds.rootUrl
        self.source_type = ds.type
