import logging

from gql_query_builder import GqlQuery
from graphene import Schema

from dagshub.data_engine.client.mock_graphql import Query
from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)


class DataClient:

    def __init__(self, repo: str):
        # TODO: add project authentication here
        self.repo = repo
        self.schema = Schema(query=Query)

    def query(self, dataset: Dataset):
        q = self.generate_peek_query(dataset)
        logger.warning(f"Generated query: {q}")
        return self.schema.execute("{ hello }")

    def generate_peek_query(self, dataset: Dataset) -> str:
        query_input = {
            "datasource": dataset.source.id,
            "first": 100,
            "filter": dataset._ds_query.serialize_graphql()
        }
        query_filter = dataset._ds_query.serialize_graphql()
        if query_filter is not None:
            query_input["filter"] = query_filter
        # filter_res =
        edges_fields = GqlQuery().fields(["cursor"], name="edges").generate()
        query = GqlQuery().query("datasourceQuery",
                                 input=query_input).fields([edges_fields])

        return query.generate()
