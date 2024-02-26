from dataclasses import dataclass
import functools
from typing import Any, Dict, List
from dagshub.data_engine.client.query_builder import GqlQuery


class GqlIntrospections:
    @staticmethod
    @functools.lru_cache()
    def obj_fields() -> str:
        q = (
            GqlQuery()
            .operation("query", name="introspection")
            .query("__schema")
            .fields(
                [
                    GqlQuery()
                    .fields(
                        name="types",
                        fields=[
                            "name",
                            GqlQuery()
                            .fields(
                                name="inputFields",
                                fields=["name", GqlQuery().fields(name="type", fields=["name"]).generate()],
                            )
                            .generate(),
                            GqlQuery()
                            .fields(
                                name="fields",
                                fields=["name", GqlQuery().fields(name="type", fields=["name"]).generate()],
                            )
                            .generate(),
                        ],
                    )
                    .generate()
                ]
            )
            .generate()
        )
        return q


@dataclass
class Field:
    name: str


@dataclass
class IntrospectionType:
    name: str
    inputFields: List[Field]
    fields: List[Field]

    def __hash__(self):
        return hash(self.hash_str())

    def hash_str(self):
        return self.name + "".join([f.name for f in self.fields]) + "".join([f.name for f in self.inputFields])


@dataclass
class TypesIntrospection:
    types: List[IntrospectionType]

    def __hash__(self):
        return hash("".join([t.hash_str() for t in self.types]))


class Validators:
    @staticmethod
    def query_input_validator(params: Dict[str, Any], query_input_introspection: TypesIntrospection):
        introspect_query_input_fields = Validators.get_fields(query_input_introspection, "QueryInput", "inputFields")

        # Get sent fields
        query_input = params.get("queryInput")
        if query_input is None:
            return
        sent_fields = query_input.keys()
        # Check serialized query input fields exist in introspection
        if not all([f in introspect_query_input_fields for f in sent_fields]):
            unsupported_fields = [f for f in sent_fields if f not in introspect_query_input_fields]
            raise ValueError(f"QueryInput fields are not supported: {unsupported_fields}")

    @staticmethod
    def get_fields(
        datapoints_connection_introspection: TypesIntrospection, type_name: str, attr: str = "fields"
    ) -> List[str]:
        datapoints_connection_fields = [f for f in datapoints_connection_introspection.types if f.name == type_name]
        if len(datapoints_connection_fields) == 0:
            raise ValueError(f"{type_name} is not defined")
        datapoints_connection_fields = getattr(datapoints_connection_fields[0], attr)
        if datapoints_connection_fields is None:
            raise ValueError(f"{type_name} is not defined")
        datapoints_connection_fields = [f.name for f in datapoints_connection_fields]
        return datapoints_connection_fields

    @staticmethod
    def filter_supported_fields(
        fields: List[str], response_obj_name: str, introspection: TypesIntrospection
    ) -> List[str]:
        root_fields = [f.split(" ")[0] for f in fields]
        supported_fields = Validators.get_fields(introspection, response_obj_name)
        return [fields[i] for i, rf in enumerate(root_fields) if rf in supported_fields]
