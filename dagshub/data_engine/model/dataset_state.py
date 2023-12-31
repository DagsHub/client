import json
from dataclasses import dataclass
from typing import Dict, Optional, Union

from dagshub.data_engine.client.models import DatasetResult
from dagshub.data_engine.model.query import DatasourceQuery


@dataclass
class DatasetState:
    """
    Information about the Dataset.

    Dataset is a Datasource with a Query applied on it.
    """

    dataset_id: Union[str, int]
    """
    ID of the dataset
    """
    dataset_name: str
    """
    Name of the dataset
    """
    datasource_id: Union[str, int]
    """
    ID of the datasource with which this dataset is associated
    """
    query: Optional[DatasourceQuery] = None
    """
    Query of this dataset
    """

    @staticmethod
    def from_dataset_query(
        dataset_id: int, dataset_name: str, datasource_id: int, dataset_query: Union[Dict, str]
    ) -> "DatasetState":
        if type(dataset_query) is str:
            dataset_query = json.loads(dataset_query)
        res = DatasetState(dataset_id=dataset_id, dataset_name=dataset_name, datasource_id=datasource_id)
        res.query = DatasourceQuery.deserialize(dataset_query)
        return res

    @staticmethod
    def from_gql_dataset_result(dataset_result: DatasetResult) -> "DatasetState":
        return DatasetState.from_dataset_query(
            dataset_id=dataset_result.id,
            dataset_name=dataset_result.name,
            datasource_id=dataset_result.datasource.id,
            dataset_query=dataset_result.datasetQuery,
        )
