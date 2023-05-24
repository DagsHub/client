import functools
from typing import Any, Dict, List, Union

from gql_query_builder import GqlQuery

from dagshub.data_engine.client.dataclasses import DataSourceType


class GqlMutations:

    @staticmethod
    @functools.lru_cache
    def create_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="createDataSource",
            input={
                "$name": "String!",
                "$url": "String!",
                "$dsType": "DatasourceType!"
            }
        ).query(
            "createDataSource",
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
    def create_datasource_params(name: str, url: str, ds_type: DataSourceType):
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
                "$dataSource": "ID!",
                "$dataPoints": "[DataPointMetadataInput!]!"
            }
        ).query(
            "updateMetadata",
            input={
                "dataSource": "$dataSource",
                "dataPoints": "$dataPoints"
            }
        ).fields([
            "path",
            "metadata {key value}"
        ]).generate()
        return q

    @staticmethod
    def update_metadata_params(datasource_id: Union[int, str], datapoints: List[Dict[str, Any]]):
        return {
            "dataSource": datasource_id,
            "dataPoints": datapoints,
        }

    @staticmethod
    @functools.lru_cache()
    def delete_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="deleteDatasource",
            input={
                "$dataSource": "ID!",
            }
        ).query(
            "deleteDatasource",
            input={
                "dataSource": "$dataSource",
            }
        ).generate()
        return q

    @staticmethod
    def delete_datasource_params(datasource_id: Union[int, str]):
        return {
            "dataSource": datasource_id,
        }

    @staticmethod
    @functools.lru_cache()
    def rescan_datasource():
        q = GqlQuery().operation(
            "mutation",
            name="rescanDatasource",
            input={
                "$dataSource": "ID!",
            }
        ).query(
            "rescanDatasource",
            input={
                "dataSource": "$dataSource",
            }
        ).generate()
        return q

    @staticmethod
    @functools.lru_cache()
    def rescan_datasource_params(datasource_id: Union[int, str]):
        return {
            "dataSource": datasource_id,
        }
