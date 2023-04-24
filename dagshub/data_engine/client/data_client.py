import logging
import typing
from dataclasses import dataclass
from typing import Any, Optional, List, Dict

import pandas as pd
import gql
from gql_query_builder import GqlQuery
from graphene import Schema

import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.data_engine.client.mock_graphql import Query
from dagshub.data_engine.model.dataset import Dataset, DataPointMetadataUpdateEntry
from gql.transport.requests import RequestsHTTPTransport
import dagshub.common.config

if typing.TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DataSource

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    key: str
    value: Any


@dataclass
class PeekResultEntry:
    name: str
    downloadUrl: str
    metadata: Dict[str, Any]


@dataclass
class PeekResult:
    entries: List[PeekResultEntry]

    @property
    def dataframe(self):
        self.entries = list(sorted(self.entries, key=lambda a: a.name))
        metadata_keys = set()
        names = []
        for e in self.entries:
            names.append(e.name)
            metadata_keys.update(e.metadata.keys())

        res = pd.DataFrame({"name": names})

        for key in sorted(metadata_keys):
            res[key] = [e.metadata.get(key) for e in self.entries]

        return res


class DataClient:

    def __init__(self, repo: str):
        # TODO: add project authentication here
        self.repo = repo
        self.host = config.host
        self.client = self._init_client()

    def _init_client(self):
        url = f"{self.host}/api/v1/repos/{self.repo}/data-engine/graphql"
        auth = HTTPBearerAuth(dagshub.auth.get_token(host=self.host))
        transport = RequestsHTTPTransport(url=url, auth=auth)
        client = gql.Client(transport=transport)
        return client

    def create_datasource(self, ds: "DataSource"):
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
        ])
        q = q.generate()
        params = {
            "name": ds.name,
            "url": ds.path,
            "dsType": str(ds.source_type.value),
        }
        res = self._exec(q, params)
        return res["createDataSource"]

    def peek(self, dataset: Dataset) -> PeekResult:
        resp = self._query(dataset, 10, True)
        res = PeekResult([self.edge_to_peekresult(edge) for edge in resp["datasourceQuery"]["edges"]])
        return res

    def edge_to_peekresult(self, edge: Dict) -> PeekResultEntry:
        res = PeekResultEntry(
            name=edge["node"]["name"],
            downloadUrl=edge["node"]["source"]["downloadUrl"],
            metadata={}
        )
        for meta_dict in edge["node"]["metadata"]:
            res.metadata[meta_dict["key"]] = meta_dict["value"]
        return res

    def get_datapoints(self, dataset: Dataset):
        return self._get_all(dataset, True)

    def _get_all(self, dataset: Dataset, include_metadata: bool):
        # Todo: use pagination here
        return self._query(dataset, 100, include_metadata)

    def _exec(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug(f"Executing query: {query}")
        if params is not None:
            logger.debug(f"Params: {params}")
        # TODO: what about params?
        q = gql.gql(query)
        resp = self.client.execute(q, variable_values=params)
        logger.debug(f"Got result: {resp}")
        return resp

    def _query(self, dataset: Dataset, limit: int, include_metadata: bool):
        q = GqlQuery().operation(
            "query",
            name="datasourceQuery",
            input={
                "$datasource": "ID!",
                "$queryInput": "QueryInput"
            }
        ).query(
            "datasourceQuery",
            input={
                "datasource": "$datasource",
                "filter": "$queryInput"
            }
        ).fields([
            "totalCount",
            "edges { node { name source { name downloadUrl previewUrl } metadata { key value } } cursor }"
        ]).generate()

        params = {
            "datasource": dataset.source.id,
            "queryInput": {"query": dataset._query.serialize_graphql()}
        }

        return self._exec(q, params)

    def add_metadata(self, dataset: Dataset, entries: List[DataPointMetadataUpdateEntry]):
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
            "name",
            "source {name downloadUrl previewUrl}",
            "metadata {key value}"
        ]).generate()

        params = {
            "dataSource": dataset.source.id,
            "dataPoints": [e.to_dict() for e in entries],
        }

        return self._exec(q, params)

    def save_dataset(self, dataset: Dataset):
        raise NotImplementedError

    @staticmethod
    def _datasource_query(dataset: Dataset, limit: int, include_metadata: bool = False) -> str:
        query_input = {
            "datasource": dataset.source.id,
            "first": limit,
        }
        query_filter = dataset._query.serialize_graphql()
        if query_filter is not None:
            query_input["filter"] = query_filter

        node_fields = ["name"]
        if include_metadata:
            node_fields.append(GqlQuery().fields(["key", "value"], name="metadata").generate())
        node_fields = GqlQuery().fields(node_fields, name="node").generate()

        edges_fields = GqlQuery().fields([node_fields], name="edges").generate()

        query = GqlQuery().query("datasourceQuery",
                                 input=query_input).fields([edges_fields])

        return query.generate()
