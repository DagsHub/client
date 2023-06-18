import enum
from dataclasses import dataclass
from typing import Dict, Any, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource


@dataclass
class Metadata:
    key: str
    value: Any


@dataclass
class Datapoint:
    datapoint_id: str
    path: str
    metadata: Dict[str, Any]

    def download_url(self, ds: "Datasource"):
        return ds.source.raw_path(self)

    @staticmethod
    def from_gql_edge(edge: Dict) -> "Datapoint":
        res = Datapoint(
            datapoint_id=edge["node"]["id"],
            path=edge["node"]["path"],
            metadata={}
        )
        for meta_dict in edge["node"]["metadata"]:
            res.metadata[meta_dict["key"]] = meta_dict["value"]
        return res

    def to_dict(self, ds: "Datasource", metadata_keys: List[str]) -> Dict[str, Any]:
        res_dict = {"name": self.path, "datapoint_id": self.datapoint_id, "dagshub_download_url": self.download_url(ds)}
        res_dict.update({key: self.metadata.get(key) for key in metadata_keys})
        return res_dict


class IntegrationStatus(enum.Enum):
    VALID = "VALID"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    MISSING = "MISSING"


class PreprocessingStatus(enum.Enum):
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    UNKNOWN = ""  # TODO: delete once it's returned consistently


class DatasourceType(enum.Enum):
    BUCKET = "BUCKET"
    REPOSITORY = "REPOSITORY"
    CUSTOM = "CUSTOM"


@dataclass
class DatasourceResult:
    id: Union[str, int]
    name: str
    rootUrl: str
    integrationStatus: IntegrationStatus
    preprocessingStatus: PreprocessingStatus
    type: DatasourceType


@dataclass
class DatasetResult:
    id: Union[str, int]
    name: str
    datasource: DatasourceResult
    datasetQuery: str


@dataclass
class QueryResult:
    entries: List[Datapoint]
    """ List of downloaded entries."""
    datasource: "Datasource"

    @property
    def dataframe(self):
        import pandas as pd
        metadata_keys = set()
        for e in self.entries:
            metadata_keys.update(e.metadata.keys())

        metadata_keys = list(sorted(metadata_keys))
        return pd.DataFrame.from_records([dp.to_dict(self.datasource, metadata_keys) for dp in self.entries])

    @staticmethod
    def from_gql_query(query_resp: Dict[str, Any], datasource: "Datasource") -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([], datasource)
        if query_resp["edges"] is None:
            return QueryResult([], datasource)
        return QueryResult([Datapoint.from_gql_edge(edge) for edge in query_resp["edges"]], datasource)
