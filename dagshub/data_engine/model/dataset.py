import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from dagshub.data_engine.model.datapoints import DatapointCollection
from dagshub.data_engine.model.query import Query

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DataSource

logger = logging.getLogger(__name__)

class Dataset:

    def __init__(self, datasource: "DataSource", query: Optional[Query] = None):
        self._source = datasource
        if query is None:
            query = Query(self)
        self._ds_query = query
        self._include_list: Optional[DatapointCollection] = None
        self._exclude_list: Optional[DatapointCollection] = None
        self._subset_list: Optional[DatapointCollection] = None



    def include(self):
        pass

    def exclude(self):
        pass

    def subset(self):
        pass

    def query(self, query_dict: Dict[str, Any]):
        """Composites a new dataset out of this dataset's query and the new query"""
        new_query = Query.from_dict(self, query_dict)
        return Dataset(source=self._source, query=self._ds_query.compose(new_query))

    def peek(self):
        return self._source.client.query(self)


    def save_dataset(self):
        logger.info(f"Saving dataset")

