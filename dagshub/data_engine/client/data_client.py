from graphene import Schema

from dagshub.data_engine.client.mock_graphql import Query
from dagshub.data_engine.model.dataset import Dataset


class DataClient:

    def __init__(self, repo: str):
        # TODO: add project authentication here
        self.repo = repo
        self.schema = Schema(query=Query)

    def query(self, dataset: Dataset):
        return self.schema.execute("{ hello }")
