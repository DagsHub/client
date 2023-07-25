import functools
from typing import Any, Dict, List, Union

from dagshub.data_engine.client.query_builder import GqlQuery

from dagshub.data_engine.client.models import DatasourceType


class GqlMutations:

    @staticmethod
    @functools.lru_cache()
    def create_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="createDatasource",
            input={
                "$name": "String!",
                "$url": "String!",
                "$dsType": "DatasourceType!"
            }
        ).query(
            "createDatasource",
            input={
                "name": "$name",
                "url": "$url",
                "dsType": "$dsType"
            }
        ).fields([
            "id",
            "name",
            "rootUrl",
            "integrationStatus",
            "preprocessingStatus",
            "type"
        ]).generate()
        return q

    @staticmethod
    def create_datasource_params(name: str, url: str, ds_type: DatasourceType):
        return {
            "name": name,
            "url": url,
            "dsType": str(ds_type.value)
        }

    @staticmethod
    @functools.lru_cache()
    def update_metadata():
        q = GqlQuery().operation(
            "mutation",
            name="updateMetadata",
            input={
                "$datasource": "ID!",
                "$datapoints": "[DatapointMetadataInput!]!"
            }
        ).query(
            "updateMetadata",
            input={
                "datasource": "$datasource",
                "datapoints": "$datapoints"
            }
        ).fields([
            "path",
        ]).generate()
        return q

    @staticmethod
    def update_metadata_params(datasource_id: Union[int, str], datapoints: List[Dict[str, Any]]):
        return {
            "datasource": datasource_id,
            "datapoints": datapoints,
        }

    @staticmethod
    @functools.lru_cache()
    def delete_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="deleteDatasource",
            input={
                "$id": "ID!",
            }
        ).query(
            "deleteDatasource",
            input={
                "id": "$id",
            }
        ).fields([
            "id",
            "name",
            "rootUrl",
            "integrationStatus",
            "preprocessingStatus",
            "type",
        ]).generate()
        return q

    @staticmethod
    def delete_datasource_params(datasource_id: Union[int, str]):
        return {
            "id": datasource_id,
        }

    @staticmethod
    @functools.lru_cache()
    def scan_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="scanDatasource",
            input={
                "$id": "ID!",
            }
        ).query(
            "scanDatasource",
            input={
                "id": "$id",
            }
        ).fields([
            "id",
            "name",
            "rootUrl",
            "integrationStatus",
            "preprocessingStatus",
            "type",
        ]).generate()
        return q

    @staticmethod
    @functools.lru_cache()
    def scan_datasource_params(datasource_id: Union[int, str]):
        return {
            "id": datasource_id,
        }

    @staticmethod
    @functools.lru_cache()
    def save_dataset():
        q = GqlQuery().operation(
            "mutation",
            name="saveDataset",
            input={
                "$datasource": "ID!",
                "$name": "String!",
                "$filter": "QueryInput!"
            }
        ).query(
            "saveDataset",
            input={
                "datasource": "$datasource",
                "name": "$name",
                "filter": "$filter"
            }
        ).fields([
            "id",
            "name",
            "createdAt",
        ]).generate()
        return q

    @staticmethod
    def save_dataset_params(datasource_id: Union[int, str], name: str, query_input: Dict[str, Any]):
        return {
            "datasource": datasource_id,
            "name": name,
            "filter": query_input,
        }
