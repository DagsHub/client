import functools
from typing import Optional, Any, Dict, Union

from dagshub.data_engine.client.gql_introspections import Validators
from dagshub.data_engine.client.query_builder import GqlQuery


class GqlQueries:
    @staticmethod
    @functools.lru_cache()
    def datasource() -> GqlQuery:
        q = (
            GqlQuery()
            .operation("query", name="datasource", input={"$id": "ID", "$name": "String"})
            .query(
                "datasource",
                input={
                    "id": "$id",
                    "name": "$name",
                },
            )
            .fields(
                [
                    "id",
                    "name",
                    "rootUrl",
                    "integrationStatus",
                    "preprocessingStatus",
                    "metadataFields {name valueType multiple tags}" "type",
                ]
            )
        )
        return q

    @staticmethod
    def datasource_params(id: Optional[Union[int, str]], name: Optional[str]) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
        }

    @staticmethod
    @functools.lru_cache()
    def datasource_query(include_metadata: bool) -> GqlQuery:
        metadata_fields = "metadata { key value }" if include_metadata else ""
        q = (
            GqlQuery()
            .operation(
                "query",
                name="datasourceQuery",
                input={
                    "$datasource": "ID!",
                    "$queryInput": "QueryInput",
                    "$first": "Int",
                    "$after": "String",
                },
            )
            .query(
                "datasourceQuery",
                input={
                    "datasource": "$datasource",
                    "filter": "$queryInput",
                    "first": "$first",
                    "after": "$after",
                },
            )
            .fields(
                [
                    f"edges {{ node {{ id path {metadata_fields} }} }}",
                    "pageInfo { hasNextPage endCursor }",
                ]
            )
        )

        q.param_validator(Validators.query_input_validator)
        return q

    @staticmethod
    def datasource_query_params(
        datasource_id: Union[int, str], query_input: Dict[str, Any], first: Optional[int], after: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "datasource": datasource_id,
            "queryInput": query_input,
            "first": first,
            "after": after,
        }

    @staticmethod
    @functools.lru_cache()
    def dataset() -> GqlQuery:
        q = (
            GqlQuery()
            .operation("query", name="dataset", input={"$id": "ID", "$name": "String"})
            .query(
                "dataset",
                input={
                    "dataset": "$id",
                    "name": "$name",
                },
            )
            .fields(
                [
                    "id",
                    "name",
                    "datasource {id name rootUrl integrationStatus preprocessingStatus "
                    "metadataFields {name valueType multiple tags} type}",
                    "datasetQuery",
                ]
            )
        )
        return q

    @staticmethod
    def dataset_params(id: Optional[Union[int, str]], name: Optional[str]) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
        }
