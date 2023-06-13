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
    path: str
    metadata: Dict[str, Any]

    def download_url(self, ds: "Datasource"):
        return ds.source.raw_path(self)

    @staticmethod
    def from_gql_edge(edge: Dict) -> "Datapoint":
        res = Datapoint(
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
class QueryResult:
    entries: List[Datapoint]
    """ List of downloaded entries."""
    datasource: "Datasource"

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
    def from_gql_query(query_resp: Dict[str, Any], datasource: "Datasource") -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([], datasource)
        if query_resp["edges"] is None:
            return QueryResult([], datasource)
        return QueryResult([Datapoint.from_gql_edge(edge) for edge in query_resp["edges"]], datasource)

    def _extend_from_gql_query(self, query_resp: Dict[str, Any]):
        self.entries += self.from_gql_query(query_resp, self.datasource).entries

    def as_dataset(self, flavor, strategy='background', **kwargs):
        """
        flavor: torch|tensorflow
        download: preload|background|lazy; default: background
        """
        if flavor == 'torch':
            from .dataset import PyTorchDataset
            return PyTorchDataset(self, strategy, **kwargs)
        elif flavor == 'tensorflow': raise NotImplementedError('coming soon')
        else: raise ValueError('supported flavors are ["torch", "tensorflow"]')

    def as_dataloader(self, flavor, strategy='background', **kwargs):
        if flavor == 'torch':
            from torch.utils.data import DataLoader
            return DataLoader(self.as_dataset(flavor, strategy), **kwargs)
        elif flavor == 'tensorflow': raise NotImplementedError('coming soon')
        else: raise ValueError('supported flavors are ["torch", "tensorflow"]')
