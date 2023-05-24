import functools
from typing import Any, Dict, List, Union

from gql_query_builder import GqlQuery

from dagshub.data_engine.client.dataclasses import DatasourceType


class GqlMutations:

    @staticmethod
    @functools.lru_cache
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
    @functools.lru_cache
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
            "metadata {key value}"
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
                "$datasource": "ID!",
            }
        ).query(
            "deleteDatasource",
            input={
                "datasource": "$datasource",
            }
        ).generate()
        return q

    @staticmethod
    def delete_datasource_params(datasource_id: Union[int, str]):
        return {
            "datasource": datasource_id,
        }

    @staticmethod
    @functools.lru_cache()
    def rescan_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="rescanDatasource",
            input={
                "$datasource": "ID!",
            }
        ).query(
            "rescanDatasource",
            input={
                "datasource": "$datasource",
            }
        ).generate()
        return q

    @staticmethod
    @functools.lru_cache()
    def rescan_datasource_params(datasource_id: Union[int, str]):
        return {
            "datasource": datasource_id,
        }
