import functools
from typing import Any, Dict, List

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
    def update_metadata_params(datasource_id: str, datapoints: List[Dict[str, Any]]):
        return {
            "dataSource": datasource_id,
            "dataPoints": datapoints,
        }
