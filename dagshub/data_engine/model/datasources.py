import logging
import enum
import urllib.parse
from dataclasses import dataclass, field

from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)


class DataSourceType(enum.Enum):
    BUCKET = "BUCKET"
    REPOSITORY = "REPOSITORY"
    CUSTOM = "CUSTOM"


@dataclass
class DataSource:
    id: str = field(init=False)
    source_type: DataSourceType
    repo: str
    path: str
    name: str
    client: DataClient = field(init=False)

    def create(self):
        datasource = self.client.create_datasource(self)
        logging.debug(f"datasource: {datasource}")
        self.id = datasource["id"]

    def __post_init__(self):
        self.client = DataClient(self.repo)
        # TODO: actually query for the id
        self.id = "1"

    def content_path(self, path: str) -> str:
        if self.source_type == DataSourceType.BUCKET:
            parsed_path = urllib.parse.urlparse(self.path)
            return f"{self.client.host}/api/v1/repos/{self.repo}/storage/content/{parsed_path.scheme}/" \
                   f"{parsed_path.hostname}/{parsed_path.path}/{path}"
        raise NotImplementedError

    def raw_path(self, path: str) -> str:
        if self.source_type == DataSourceType.BUCKET:
            parsed_path = urllib.parse.urlparse(self.path)
            return f"{self.client.host}/api/v1/repos/{self.repo}/storage/raw/{parsed_path.scheme}/" \
                   f"{parsed_path.path}/{path}"
        raise NotImplementedError


def from_bucket(name, repo, bucket_url: str) -> Dataset:
    # TODO: add "create if not exists" capability
    ds = DataSource(DataSourceType.BUCKET, repo, bucket_url, name=name)
    return Dataset(datasource=ds)


def from_repo(repo, path: str, revision: str = "main") -> Dataset:
    return Dataset(DataSource(DataSourceType.REPOSITORY, repo, f"{revision}/{path}"))


def from_dataset(repo, dataset_name: str) -> Dataset:
    return Dataset(DataSource(DataSourceType.CUSTOM, repo, dataset_name))


__all__ = [
    from_bucket,
    from_repo,
    from_dataset,
]
