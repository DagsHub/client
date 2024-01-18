import functools
from typing import Optional, Any, Dict, Union

from dagshub.data_engine.client.query_builder import GqlQuery


class GqlQueries:
    @staticmethod
    @functools.lru_cache()
    def datasource() -> str:
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
            .generate()
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

        def query_input_validator(params: Dict[str, Any], introspection_dict: Dict[str, Any]):
            # Get fields of input field QueryInput
            introspect_query_input_fields = [
                f for f in introspection_dict["__schema"]["types"]
                if f["name"] == "QueryInput"
            ]
            if len(introspect_query_input_fields) == 0:
                raise ValueError("QueryInput is not defined")
            introspect_query_input_fields = introspect_query_input_fields[0].get("inputFields")
            if introspect_query_input_fields is None:
                raise ValueError("QueryInput is not defined")
            introspect_query_input_fields = [f["name"] for f in introspect_query_input_fields]

            # Get sent fields
            query_input = params.get("queryInput")
            if query_input is None:
                return
            sent_fields = query_input.keys()
            # Check serialized query input fields exist in introspection
            if not all([f in introspect_query_input_fields for f in sent_fields]):
                unsupported_fields = [f for f in sent_fields if f not in introspect_query_input_fields]
                raise ValueError(f"QueryInput fields are not supported: {unsupported_fields}")
        q.param_validator(query_input_validator)
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
    def dataset() -> str:
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
            .generate()
        )
        return q

    @staticmethod
    def dataset_params(id: Optional[Union[int, str]], name: Optional[str]) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
        }
