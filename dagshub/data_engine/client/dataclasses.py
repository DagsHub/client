import enum
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class Metadata:
    key: str
    value: Any


@dataclass
class DataPoint:
    path: str
    metadata: Dict[str, Any]

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
    id: str
    name: str
    rootUrl: str
    integrationStatus: IntegrationStatus
    type: DataSourceType


@dataclass
class QueryResult:
    # List of downloaded entries. In case of .head() calls the number entries will be less than totalCount
    entries: List[DataPoint]

    @property
    def dataframe(self):
        import pandas as pd
        self.entries = list(sorted(self.entries, key=lambda a: a.path))
        metadata_keys = set()
        names = []
        for e in self.entries:
            names.append(e.path)
            metadata_keys.update(e.metadata.keys())

        res = pd.DataFrame({"name": names})

        for key in sorted(metadata_keys):
            res[key] = [e.metadata.get(key) for e in self.entries]

        return res

    @staticmethod
    def from_gql_query(query_resp: Dict[str, Any]) -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([])
        return QueryResult([DataPoint.from_gql_edge(edge) for edge in query_resp["edges"]])

    def _extend_from_gql_query(self, query_resp: Dict[str, Any]):
        self.entries += self.from_gql_query(query_resp).entries
