import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from dataclasses_json import dataclass_json

from dagshub.data_engine.model.query import Query, _metadataTypeLookup

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DataSource

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class DataPointMetadataUpdateEntry(json.JSONEncoder):
    url: str
    key: str
    value: str
    valueType: str


class Dataset:

    def __init__(self, datasource: "DataSource", query: Optional[Query] = None):
        self._source = datasource
        if query is None:
            query = Query(self)
        self._ds_query = query
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

    def _query(self, query_operand="and", param_operand="and", **query_params):
        """
        Composites a new dataset out of this dataset's query and the new query

        query_operand decides the operand between the dataset's query and the new query
        filter_operand decides the operand used between the query parameters
        """

        new_query = Query.from_query_params(self, param_operand, **query_params)
        return Dataset(datasource=self._source, query=self._ds_query.compose(new_query, query_operand))

    def query(self, param_operand="and", **query_params):
        return self.and_query(param_operand, **query_params)

    def and_query(self, param_operand="and", **query_params):
        return self._query("and", param_operand, **query_params)

    def or_query(self, param_operand="and", **query_params):
        return self._query("or", param_operand, **query_params)

    def peek(self):
        return self._source.client.get_datapoints(self)

    @contextmanager
    def metadata_context(self) -> "MetadataContextManager":
        ctx = MetadataContextManager(self)
        yield ctx
        self.source.client.add_metadata(self, ctx.get_metadata_entries())

    def __str__(self):
        return f"<Dataset source:{self._source}, query: {self._ds_query}>"

    def save_dataset(self):
        logger.info(f"Saving dataset")
        raise NotImplementedError


class MetadataContextManager:
    def __init__(self, dataset: Dataset):
        self._dataset = dataset
        self._metadata_entries: List[DataPointMetadataUpdateEntry] = []

    def update_metadata(self, datapoints: List[str], metadata: Dict[str, Any]):
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
