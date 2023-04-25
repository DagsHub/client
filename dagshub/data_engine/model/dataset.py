import json
import logging
import os.path
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import fiftyone as fo
import httpx
from dataclasses_json import dataclass_json

import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.data_engine.model.errors import WrongOperatorError, WrongOrderError, DatasetFieldComparisonError
from dagshub.data_engine.model.query import DatasetQuery, _metadataTypeLookup

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DataSource
    from dagshub.data_engine.client.data_client import PeekResult

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class DataPointMetadataUpdateEntry(json.JSONEncoder):
    url: str
    key: str
    value: str
    valueType: str



class Dataset:

    def __init__(self, datasource: "DataSource", query: Optional[DatasetQuery] = None):
        self._source = datasource
        if query is None:
            query = DatasetQuery(self)
        self._query = query
        self._include_list: Optional[str] = None
        self._exclude_list: Optional[str] = None

    @property
    def source(self):
        return self._source

    def include(self):
        """Force adds datapoints to the returned set. They will show up even if they don't pass the query"""
        raise NotImplementedError

    def exclude(self):
        """Excludes datapoints from the returned set. They will not show up even if they pass the query"""
        raise NotImplementedError

    # def _query(self, query_operand="and", param_operand="and", **query_params):
    #     """
    #     Composites a new dataset out of this dataset's query and the new query
    #
    #     query_operand decides the operand between the dataset's query and the new query
    #     filter_operand decides the operand used between the query parameters
    #     """
    #
    #     new_query = Query.from_query_params(self, param_operand, **query_params)
    #     return Dataset(datasource=self._source, query=self._ds_query.compose(new_query, query_operand))

    def __deepcopy__(self, memodict={}) -> "Dataset":
        return Dataset(self._source, self._query.__deepcopy__())

    def get_query(self):
        return self._query

    #
    # def and_query(self, param_operand="and", **query_params):
    #     return self._query("and", param_operand, **query_params)
    #
    # def or_query(self, param_operand="and", **query_params):
    #     return self._query("or", param_operand, **query_params)

    def peek(self) -> "PeekResult":
        return self._source.client.peek(self)

    @contextmanager
    def metadata_context(self) -> "MetadataContextManager":
        ctx = MetadataContextManager(self)
        yield ctx
        self.source.client.add_metadata(self, ctx.get_metadata_entries())

    def __str__(self):
        return f"<Dataset source:{self._source}, query: {self._query}>"

    def save_dataset(self):
        logger.info(f"Saving dataset")
        raise NotImplementedError

    def to_voxel51_dataset(self) -> fo.Dataset:
        logger.info("Migrating dataset to voxel51")
        name = self._source.name
        ds: fo.Dataset = fo.Dataset(name)
        # ds.persistent = True
        dataset_location = os.path.join(Path.home(), "dagshub_datasets")
        os.makedirs(dataset_location, exist_ok=True)
        logger.info("Downloading files...")
        # Load the dataset from the query

        # FIXME: shouldnt use peek here, but only peekresult has the dataframe
        datapoints = self.peek()

        host = config.host
        client = httpx.Client(auth=HTTPBearerAuth(dagshub.auth.get_token(host=host)))

        samples = []

        # TODO: parallelize this with some async magic
        for datapoint in datapoints.entries:
            file_url = datapoint.downloadUrl
            resp = client.get(file_url)
            assert resp.status_code == 200
            # TODO: doesn't work with nesting
            filename = file_url.split("/")[-1]
            filepath = os.path.join(dataset_location, filename)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            sample = fo.Sample(filepath=filepath)
            sample["url"] = file_url
            for k, v in datapoint.metadata.items():
                sample[k] = v
            samples.append(sample)
        logger.info(f"Downloaded {len(datapoints.dataframe['name'])} file(s) into {dataset_location}")
        ds.add_samples(samples)
        return ds

    def __getitem__(self, column_or_query: Union[str, "Dataset"]):
        new_ds = self.__deepcopy__()
        if type(column_or_query) is str:
            new_ds._query = DatasetQuery(new_ds, column_or_query)
            return new_ds
        else:
            # "index" is a dataset with a query - compose with "and"
            if self._query.is_empty:
                new_ds._query = column_or_query._query
                return new_ds
            else:
                return column_or_query.__and__(self)

    def __gt__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("gt", other)

    def __ge__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("ge", other)

    def __le__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("le", other)

    def __lt__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("lt", other)

    def __eq__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("eq", other)

    def __ne__(self, other: Union[int, float, str]):
        self._test_not_comparing_other_ds(other)
        return self.add_query_op("ne", other)

    def __contains__(self, item: Union[int, float, str]):
        raise WrongOperatorError("Use `ds.contains(a)` for querying instead of `a in contains`")

    def contains(self, item: Union[int, float, str]):
        self._test_not_comparing_other_ds(item)
        return self.add_query_op("contains", item)

    def __and__(self, other: "Dataset"):
        return self.add_query_op("and", other)

    def __or__(self, other: "Dataset"):
        return self.add_query_op("or", other)

    def __rand__(self, other):
        if type(other) is not Dataset:
            raise WrongOrderError(type(other))
        raise NotImplementedError

    def __ror__(self, other):
        if type(other) is not Dataset:
            raise WrongOrderError(type(other))
        raise NotImplementedError

    def add_query_op(self, op: str, other: [str, int, float, "Dataset"]) -> "Dataset":
        """
        Returns a new dataset with an added query param
        """
        new_ds = self.__deepcopy__()
        if type(other) is Dataset:
            other = other.get_query()
        new_ds._query.compose(op, other)
        return new_ds

    @staticmethod
    def _test_not_comparing_other_ds(other):
        if type(other) is Dataset:
            raise DatasetFieldComparisonError()


class MetadataContextManager:
    def __init__(self, dataset: Dataset):
        self._dataset = dataset
        self._metadata_entries: List[DataPointMetadataUpdateEntry] = []

    def update_metadata(self, datapoints: Union[List[str], str], metadata: Dict[str, Any]):
        if isinstance(datapoints, str):
            datapoints = [datapoints]
        for dp in datapoints:
            for k, v in metadata.items():
                self._metadata_entries.append(DataPointMetadataUpdateEntry(
                    url=dp,
                    key=k,
                    value=str(v),
                    # todo: preliminary type check
                    valueType=_metadataTypeLookup[type(v)]
                ))

    def get_metadata_entries(self):
        return self._metadata_entries
