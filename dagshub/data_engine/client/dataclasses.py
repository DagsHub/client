import enum
from dataclasses import dataclass
from typing import Dict, Any, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import DataSource


@dataclass
class Metadata:
    key: str
    value: Any


@dataclass
class DataPoint:
    path: str
    metadata: Dict[str, Any]

    def download_url(self, ds: "DataSource"):
        return ds.source.raw_path(self)

    @staticmethod
    def from_gql_edge(edge: Dict) -> "DataPoint":
        res = DataPoint(
            path=edge["node"]["path"],
            metadata={}
        )
        for meta_dict in edge["node"]["metadata"]:
            res.metadata[meta_dict["key"]] = meta_dict["value"]
        return res


class IntegrationStatus(enum.Enum):
    VALID = "VALID"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    MISSING = "MISSING"


class DataSourceType(enum.Enum):
    BUCKET = "BUCKET"
    REPOSITORY = "REPOSITORY"
    CUSTOM = "CUSTOM"


@dataclass
class DataSourceResult:
    id: Union[str, int]
    name: str
    rootUrl: str
    integrationStatus: IntegrationStatus
    type: DataSourceType


@dataclass
class QueryResult:
    entries: List[DataPoint]
    """ List of downloaded entries."""
    datasource: "DataSource"

    @property
    def dataframe(self):
        import pandas as pd
        self.entries = list(sorted(self.entries, key=lambda a: a.path))
        metadata_keys = set()
        names = []
        urls = []
        for e in self.entries:
            names.append(e.path)
            urls.append(e.download_url(self.datasource))
            metadata_keys.update(e.metadata.keys())

        res = pd.DataFrame({"name": names, "dagshub_download_url": urls})

        for key in sorted(metadata_keys):
            res[key] = [e.metadata.get(key) for e in self.entries]

        return res

    @staticmethod
    def from_gql_query(query_resp: Dict[str, Any], datasource: "DataSource") -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([], datasource)
        return QueryResult([DataPoint.from_gql_edge(edge) for edge in query_resp["edges"]], datasource)

    def _extend_from_gql_query(self, query_resp: Dict[str, Any]):
        self.entries += self.from_gql_query(query_resp, self.datasource).entries
