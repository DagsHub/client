import logging
import enum
from dataclasses import dataclass, field

from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)


class DataSourceType(enum.Enum):
    BUCKET = 1
    REPO = 2
    DATASET = 3


@dataclass
class DataSource:
    id: str = field(init=False)
    source_type: DataSourceType
    repo: str
    path: str
    name: str
    client: DataClient = field(init=False)

    def create(self):
        self.client = DataClient(self.repo)
        datasource = self.client.create_datasource(self.name, self.path)
        logging.debug(f"datasource: {datasource}")
        self.id = datasource["id"]

    def __post_init__(self):
        self.client = DataClient(self.repo)
    #     datasource = self.client.create_datasource(self.name, self.path)
    #     logging.debug(f"res: {res}")
    #     self.id = datasource["id"]


def from_bucket(name, repo, bucket_url: str) -> Dataset:
    ds = DataSource(DataSourceType.BUCKET, repo, bucket_url, name=name)
    ds.create()
    return Dataset(datasource=ds)


def from_repo(repo, path: str, revision: str = "main") -> Dataset:
    return Dataset(DataSource(DataSourceType.REPO, repo, f"{revision}/{path}"))


def from_dataset(repo, dataset_name: str) -> Dataset:
    return Dataset(DataSource(DataSourceType.DATASET, repo, dataset_name))


__all__ = [
    from_bucket,
    from_repo,
    from_dataset,
]
