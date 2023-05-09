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
class DataPoint:
    name: str
    downloadUrl: str
    metadata: Dict[str, Any]

    @staticmethod
    def from_gql_edge(edge: Dict) -> "DataPoint":
        res = DataPoint(
            name=edge["node"]["name"],
            downloadUrl=edge["node"]["source"]["downloadUrl"],
            metadata={}
        )
        for meta_dict in edge["node"]["metadata"]:
            res.metadata[meta_dict["key"]] = meta_dict["value"]
        return res


@dataclass
class DataPointCollection:
    entries: List[DataPoint]

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

    @staticmethod
    def from_gql_query(query_resp: Dict[str, Any]) -> "DataPointCollection":
        if query_resp["totalCount"] == 0:
            return DataPointCollection([])
        return DataPointCollection([DataPoint.from_gql_edge(edge) for edge in query_resp["edges"]])

    def extend_from_gql_query(self, query_resp: Dict[str, Any]):
        self.entries += self.from_gql_query(query_resp).entries


class DataClient:
    HEAD_QUERY_SIZE = 10
    FULL_LIST_PAGE_SIZE = 100

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

    def head(self, dataset: Dataset) -> DataPointCollection:
        resp = self._datasourceQuery(dataset, True, self.HEAD_QUERY_SIZE)
        return DataPointCollection.from_gql_query(resp)

    def get_datapoints(self, dataset: Dataset) -> DataPointCollection:
        return self._get_all(dataset, True)

    def _get_all(self, dataset: Dataset, include_metadata: bool) -> DataPointCollection:
        has_next_page = True
        after = None
        res = DataPointCollection([])
        while has_next_page:
            resp = self._datasourceQuery(dataset, include_metadata, self.FULL_LIST_PAGE_SIZE, after)
            has_next_page = resp["pageInfo"]["hasNextPage"]
            after = resp["pageInfo"]["endCursor"]
            res.extend_from_gql_query(resp)
        return res

    def _exec(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug(f"Executing query: {query}")
        if params is not None:
            logger.debug(f"Params: {params}")
        q = gql.gql(query)
        resp = self.client.execute(q, variable_values=params)
        return resp

    def _datasourceQuery(self, dataset: Dataset, include_metadata: bool, limit: Optional[int] = None,
                         after: Optional[str] = None):
        metadata_fields = "metadata { key value }" if include_metadata else ""
        q = GqlQuery().operation(
            "query",
            name="datasourceQuery",
            input={
                "$datasource": "ID!",
                "$queryInput": "QueryInput",
                "$first": "Int",
                "$after": "String",
            }
        ).query(
            "datasourceQuery",
            input={
                "datasource": "$datasource",
                "filter": "$queryInput",
                "first": "$first",
                "after": "$after",
            }
        ).fields([
            "totalCount",
            f"edges {{ node {{ name source {{ name downloadUrl previewUrl }} {metadata_fields} }} }}",
            "pageInfo { hasNextPage endCursor }"
        ]).generate()

        params = {
            "datasource": dataset.source.id,
            "queryInput": {"query": dataset.get_query().serialize_graphql()},
            "first": limit,
            "after": after,
        }

        return self._exec(q, params)["datasourceQuery"]

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
