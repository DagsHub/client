import enum
import logging
import multiprocessing.pool
from dataclasses import dataclass, field

import inspect
from pathlib import Path
from typing import Dict, Any, List, Union, TYPE_CHECKING, Optional, Tuple

from dagshub.common.util import lazy_load
from dagshub.common.helpers import http_request
from dagshub.data_engine.client.loaders.base import DagsHubDataset


tf = lazy_load("tensorflow")

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    key: str
    value: Any


autogenerated_columns = {
    "name",
    "datapoint_id",
    "dagshub_download_url",
}


@dataclass
class Datapoint:
    datapoint_id: int
    path: str
    metadata: Dict[str, Any]
    datasource: "Datasource"

    def download_url(self):
        return self.datasource.source.raw_path(self)

    def path_in_repo(self):
        return self.datasource.source.file_path(self)

    @staticmethod
    def from_gql_edge(edge: Dict, datasource: "Datasource") -> "Datapoint":
        res = Datapoint(
            datapoint_id=int(edge["node"]["id"]),
            path=edge["node"]["path"],
            metadata={},
            datasource=datasource,
        )
        for meta_dict in edge["node"]["metadata"]:
            res.metadata[meta_dict["key"]] = meta_dict["value"]
        return res

    def to_dict(self, metadata_keys: List[str]) -> Dict[str, Any]:
        res_dict = {
            "name": self.path,
            "datapoint_id": self.datapoint_id,
            "dagshub_download_url": self.download_url(),
        }
        res_dict.update({key: self.metadata.get(key) for key in metadata_keys})
        return res_dict

    def get_blob(self, column: str, cache_on_disk=True, store_value=False) -> bytes:
        """
        Returns the blob stored in the binary column

        Args:
            column: where to get the blob from
            cache_on_disk: whether to store the downloaded blob on the disk or not
            store_value: whether to store the blob in the field after acquiring it
        """
        current_value = self.metadata[column]

        if type(current_value) is bytes:
            # Bytes - it's already there!
            return current_value
        if isinstance(current_value, Path):
            # Path - assume the path exists and is already downloaded,
            #   because it's unlikely that the user has set it themselves
            with current_value.open("rb") as f:
                content = f.read()
            if store_value:
                self.metadata[column] = content
            return content

        elif type(current_value) is str:
            # String - This is probably the hash of the blob, get that from dagshub
            blob_url = self.blob_url(current_value)
            blob_location = self.blob_cache_location / current_value

            # Make sure that the cache location exists
            if cache_on_disk:
                self.blob_cache_location.mkdir(parents=True, exist_ok=True)

            content = _get_blob(blob_url, blob_location, self.datasource.source.repoApi.auth, cache_on_disk, True)
            if type(content) is str:
                raise RuntimeError(f"Error while downloading blob: {content}")

            if store_value:
                self.metadata[column] = content
            elif cache_on_disk:
                self.metadata[column] = blob_location

            return content
        else:
            raise ValueError(f"Can't extract blob metadata from value {current_value} of type {type(current_value)}")

    @property
    def blob_cache_location(self):
        return self.datasource.default_dataset_location / ".metadata_blobs"

    def blob_url(self, sha):
        return self.datasource.source.blob_path(sha)

    def _extract_blob_url_and_path(self, col: str) -> Tuple[Optional[str], Optional[Path]]:
        sha = self.metadata.get(col)
        if sha is None or type(sha) is not str:
            return None, None
        return self.blob_url(sha), self.blob_cache_location / sha


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


class MetadataFieldType(enum.Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BLOB = "BLOB"


@dataclass
class MetadataFieldSchema:
    name: str
    valueType: MetadataFieldType
    multiple: bool


@dataclass
class DatasourceResult:
    id: Union[str, int]
    name: str
    rootUrl: str
    integrationStatus: IntegrationStatus
    preprocessingStatus: PreprocessingStatus
    type: DatasourceType
    metadataFields: Optional[List[MetadataFieldSchema]]


@dataclass
class DatasetResult:
    id: Union[str, int]
    name: str
    datasource: DatasourceResult
    datasetQuery: str


@dataclass
class QueryResult:
    _entries: List[Datapoint]
    """ List of downloaded entries."""
    datasource: "Datasource"
    _datapoint_path_lookup: Dict[str, Datapoint] = field(init=False)

    def __post_init__(self):
        self._refresh_lookups()

    @property
    def entries(self):
        return self._entries

    @entries.setter
    def entries(self, value: List[Datapoint]):
        self._entries = value
        self._refresh_lookups()

    def _refresh_lookups(self):
        self._datapoint_path_lookup = {}
        for e in self.entries:
            self._datapoint_path_lookup[e.path] = e

    @property
    def dataframe(self):
        import pandas as pd

        metadata_keys = set()
        for e in self.entries:
            metadata_keys.update(e.metadata.keys())

        metadata_keys = list(sorted(metadata_keys))
        return pd.DataFrame.from_records(
            [dp.to_dict(metadata_keys) for dp in self.entries]
        )

    @staticmethod
    def from_gql_query(
        query_resp: Dict[str, Any], datasource: "Datasource"
    ) -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([], datasource)
        if query_resp["edges"] is None:
            return QueryResult([], datasource)
        return QueryResult(
            [Datapoint.from_gql_edge(edge, datasource) for edge in query_resp["edges"]],
            datasource,
        )

    def as_dataset(self, flavor, **kwargs):
        """
        ARGS:
        flavor: torch|tensorflow

        KWARGS:
        metadata_columns: columns that are returned from the metadata as part of the dataset
        strategy: preload|background|lazy; default: lazy
        savedir: location at which the dataset is stored
        processes: number of parallel processes that download the dataset
        tensorizer: auto|image|<function>
        """
        flavor = flavor.lower()
        if flavor == "torch":
            from dagshub.data_engine.client.loaders.torch import PyTorchDataset

            return PyTorchDataset(self, **kwargs)
        elif flavor == "tensorflow":
            from dagshub.data_engine.client.loaders.tf import TensorFlowDataset

            ds_builder = TensorFlowDataset(self, **kwargs)
            ds = tf.data.Dataset.from_generator(
                ds_builder.generator, output_signature=ds_builder.signature
            )
            ds.__len__ = lambda: ds_builder.__len__()
            ds.__getitem__ = ds_builder.__getitem__
            ds.builder = ds_builder
            ds.type = "tensorflow"
            return ds
        else:
            raise ValueError("supported flavors are torch|tensorflow")

    def as_dataloader(self, flavor, **kwargs):
        """
        ARGS:
        flavor: torch|tensorflow

        KWARGS:
        metadata_columns: columns that are returned from the metadata as part of the dataloader
        strategy: preload|background|lazy; default: lazy
        savedir: location at which the dataset is stored
        processes: number of parallel processes that download the dataset
        tensorizer: auto|image|<function>
        for_dataloader: bool; internal argument, that begins background dataset download after
                        the shuffle order is determined for the first epoch; default: False
        """

        def keypairs(keys):
            return {key: kwargs[key] for key in keys}

        if type(flavor) != str:
            if flavor.type == "torch":
                from dagshub.data_engine.client.loaders.torch import PyTorchDataLoader

                return PyTorchDataLoader(flavor, **kwargs)
            elif flavor.type == "tensorflow":
                from dagshub.data_engine.client.loaders.tf import TensorFlowDataLoader

                return TensorFlowDataLoader(flavor, **kwargs)

        kwargs["for_dataloader"] = True
        dataset_kwargs = set(
            list(inspect.signature(DagsHubDataset).parameters.keys())[1:]
        )
        global_kwargs = set(kwargs.keys())
        flavor = flavor.lower() if type(flavor) == str else flavor
        if flavor == "torch":
            from dagshub.data_engine.client.loaders.torch import PyTorchDataLoader

            return PyTorchDataLoader(
                self.as_dataset(
                    flavor, **keypairs(global_kwargs.intersection(dataset_kwargs))
                ),
                **keypairs(global_kwargs - dataset_kwargs),
            )
        elif flavor == "tensorflow":
            from dagshub.data_engine.client.loaders.tf import TensorFlowDataLoader

            return TensorFlowDataLoader(
                self.as_dataset(
                    flavor,
                    **keypairs(global_kwargs.intersection(dataset_kwargs)),
                ),
                **keypairs(global_kwargs - dataset_kwargs),
            )
        else:
            raise ValueError(
                "supported flavors are torch|tensorflow|<torch.utils.data.Dataset>|<tf.data.Dataset>"
            )

    def __getitem__(self, item: Union[str, int, slice]):
        """
        Gets datapoint by either its ID (int), or by its path (string)
        """
        if type(item) is str:
            return self._datapoint_path_lookup[item]
        elif type(item) is int or type(item) is slice:
            return self.entries[item]
        else:
            raise ValueError(
                f"Can't lookup datapoint using value {item} of type {type(item)}, needs to be either int or str")

    def download_binary_columns(self, *columns: str, load_into_memory=True,
                                cache_on_disk=True, num_proc: int = 32) -> "QueryResult":
        """
        Downloads data from binary-defined columns

        Args:
            columns: list of binary columns to download blobs for
            load_into_memory: Whether to load the blobs into the datapoints, or just store them on disk
                If True : the datapoints' specified columns will contain the blob data
                If False: the datapoints' specified columns will contain Path objects to the file of the downloaded blob
            cache_on_disk: Whether to cache the blobs on disk or not (valid only if load_into_memory is set to True)
                Cache location is `~/dagshub/datasets/<user>/<repo>/<datasource_id>/.metadata_blobs/`
        """
        if not load_into_memory:
            assert cache_on_disk
        for column in columns:
            logger.info(f"Downloading metadata for column {column} with {num_proc} processes")
            cache_location = self.datasource.default_dataset_location / ".metadata_blobs"

            if cache_on_disk:
                cache_location.mkdir(parents=True, exist_ok=True)

            blob_urls = list(map(lambda dp: dp._extract_blob_url_and_path(column), self.entries))
            auth = self.datasource.source.repoApi.auth
            func_args = zip(map(lambda bu: bu[0], blob_urls), map(lambda bu: bu[1], blob_urls), repeat(auth),
                            repeat(cache_on_disk), repeat(load_into_memory))
            with multiprocessing.pool.ThreadPool(num_proc) as pool:
                res = pool.starmap(_get_blob, func_args)

            for dp, binary_val in zip(self.entries, res):
                if binary_val is None:
                    continue
                dp.metadata[column] = binary_val

        return self


def _get_blob(url: Optional[str], cache_path: Optional[Path], auth, cache_on_disk, return_blob) -> Optional[
    Union[Path, str, bytes]]:
    """
    Args:
        url: url to download the blob from
        cache_path: where the cache for the blob is (laods from it if exists, stores there if it doesn't)
        auth: auth to use for getting the blob
        cache_on_disk: whether to store the downloaded blob on disk. If False we also turn off the cache checking
        return_blob: if True returns the blob of the downloaded data, if False returns the path to the file with it
    """
    if url is None:
        return None
    assert cache_path is not None

    if str(cache_path).split("/")[-1] != url.split("/")[-1]:
        raise RuntimeError(f"{cache_path} != {url}")

    if cache_on_disk and cache_path.exists():
        with cache_path.open("rb") as f:
            return f.read()

    try:
        # TODO: add retries here
        resp = http_request("GET", url, auth=auth)
        if resp.status_code >= 400:
            return f"Error while downloading binary blob (Status code {resp.status_code}): {resp.content.decode()}"
        content = resp.content
    except Exception as e:
        return f"Error while downloading binary blob: {e}"

    if cache_on_disk:
        with cache_path.open("wb") as f:
            f.write(content)

    if return_blob:
        return content
    else:
        return cache_path
