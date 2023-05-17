import logging
import typing
from typing import Any, Optional, List, Dict

import dacite
import gql
from gql.transport.requests import RequestsHTTPTransport

import dagshub.auth
import dagshub.common.config
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.data_engine.client.dataclasses import QueryResult, DataSourceResult
from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.gql_queries import GqlQueries
from dagshub.data_engine.model.datasource import DataSource, DataPointMetadataUpdateEntry

if typing.TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DataSourceState

logger = logging.getLogger(__name__)


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

    def create_datasource(self, ds: "DataSourceState") -> DataSourceResult:
        q = GqlMutations.create_datasource()

        assert ds.name is not None
        assert ds.path is not None
        assert ds.source_type is not None

        params = GqlMutations.create_datasource_params(
            name=ds.name,
            url=ds.path,
            ds_type=ds.source_type
        )
        res = self._exec(q, params)
        return dacite.from_dict(DataSourceResult, res["createDataSource"])

    def head(self, dataset: DataSource) -> QueryResult:
        resp = self._datasource_query(dataset, True, self.HEAD_QUERY_SIZE)
        return QueryResult.from_gql_query(resp)

    def get_datapoints(self, dataset: DataSource) -> QueryResult:
        return self._get_all(dataset, True)

    def _get_all(self, dataset: DataSource, include_metadata: bool) -> QueryResult:
        has_next_page = True
        after = None
        res = QueryResult([])
        while has_next_page:
            resp = self._datasource_query(dataset, include_metadata, self.FULL_LIST_PAGE_SIZE, after)
            has_next_page = resp["pageInfo"]["hasNextPage"]
            after = resp["pageInfo"]["endCursor"]
            res._extend_from_gql_query(resp)
        return res

    def _exec(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug(f"Executing query: {query}")
        if params is not None:
            logger.debug(f"Params: {params}")
        q = gql.gql(query)
        resp = self.client.execute(q, variable_values=params)
        return resp

    def _datasource_query(self, dataset: DataSource, include_metadata: bool, limit: Optional[int] = None,
                          after: Optional[str] = None):
        q = GqlQueries.datasource_query(include_metadata)

        params = GqlQueries.datasource_query_params(
            datasource_id=dataset.source.id,
            query_input=dataset.serialize_gql_query_input(),
            first=limit,
            after=after
        )

        return self._exec(q, params)["datasourceQuery"]

    def update_metadata(self, dataset: DataSource, entries: List[DataPointMetadataUpdateEntry]):
        q = GqlMutations.update_metadata()

        assert dataset.source.id is not None
        assert len(entries) > 0

        params = GqlMutations.update_metadata_params(
            datasource_id=dataset.source.id,
            datapoints=[e.to_dict() for e in entries]
        )

        return self._exec(q, params)

    def get_datasources(self, id: Optional[str], name: Optional[str]) -> List[DataSourceResult]:
        q = GqlQueries.datasource()
        params = GqlQueries.datasource_params(id=id, name=name)

        res = self._exec(q, params)["dataSource"]
        if res is None:
            return []
        return [dacite.from_dict(DataSourceResult, val) for val in res]
