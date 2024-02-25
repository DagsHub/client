from dataclasses import dataclass
import functools
from typing import Any, Dict, List
from dagshub.data_engine.client.query_builder import GqlQuery


class GqlIntrospections:
    @staticmethod
    @functools.lru_cache()
    def input_fields() -> str:
        q = (
            GqlQuery()
            .operation("query", name="introspection")
            .query("__schema").fields([
                GqlQuery().fields(name="types", fields=[
                    "name",
                    GqlQuery().fields(name="inputFields", fields=[
                        "name",
                        GqlQuery().fields(name="type", fields=[
                            "name"
                        ]).generate()
                    ]).generate()
                ]).generate()
            ]).generate()
        )
        return q


@dataclass
class InputField:
    name: str


@dataclass
class IntrospectionType:
    name: str
    inputFields: List[InputField]


@dataclass
class QueryInputIntrospection:
    types: List[IntrospectionType]


class Validators:
    @staticmethod
    def query_input_validator(params: Dict[str, Any], query_input_introspection: QueryInputIntrospection):
        # Get fields of input field QueryInput
        introspect_query_input_fields = [
            f for f in query_input_introspection.types
            if f.name == "QueryInput"
        ]
        if len(introspect_query_input_fields) == 0:
            raise ValueError("QueryInput is not defined")
        introspect_query_input_fields = introspect_query_input_fields[0].inputFields
        if introspect_query_input_fields is None:
            raise ValueError("QueryInput is not defined")
        introspect_query_input_fields = [f.name for f in introspect_query_input_fields]

        # Get sent fields
        query_input = params.get("queryInput")
        if query_input is None:
            return
        sent_fields = query_input.keys()
        # Check serialized query input fields exist in introspection
        if not all([f in introspect_query_input_fields for f in sent_fields]):
            unsupported_fields = [f for f in sent_fields if f not in introspect_query_input_fields]
            raise ValueError(f"QueryInput fields are not supported: {unsupported_fields}")
