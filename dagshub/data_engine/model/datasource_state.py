import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Union, Mapping, Any

import httpx

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
            # Assuming path format is "repo://user/repo/prefix" (branch for now assuming using default)
            # TODO: handle paths here nicer, this is a bit of a mess
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.split("/")
            path_parts = [x for x in path_parts if x != ""]
            if len(path_parts) == 1:
                repo_path = ""
            else:
                repo_path = "/".join(path_parts[1:]) + "/"
            return f"{self.client.host}/api/v1/repos/{self.repo}/{api_type}/{self._get_default_branch()}/{repo_path}{path}"

    def _get_default_branch(self):
        # todo: fix this aaaaa
        url = f"{self.client.host}/api/v1/repos/{self.repo}"
        resp = httpx.get(url)
        assert resp.status_code < 400
        return resp.json()["default_branch"]

    def _update_from_ds_result(self, ds: DataSourceResult):
        self.id = ds.id
        self.name = ds.name
        self.path = ds.rootUrl
        self.source_type = ds.type
