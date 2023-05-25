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
from dagshub.data_engine.client.dataclasses import QueryResult, DatasourceResult, DatasourceType, IntegrationStatus, \
    PreprocessingStatus
from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.gql_queries import GqlQueries
from dagshub.data_engine.model.datasource import Datasource, DatapointMetadataUpdateEntry

if typing.TYPE_CHECKING:
    from dagshub.data_engine.model.datasources import DatasourceState

logger = logging.getLogger(__name__)

_dacite_config = dacite.Config(cast=[IntegrationStatus, DatasourceType, PreprocessingStatus])


class DataClient:
    HEAD_QUERY_SIZE = 100
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

    def create_datasource(self, ds: "DatasourceState") -> DatasourceResult:
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
        return dacite.from_dict(DatasourceResult, res["createDataSource"], config=_dacite_config)

    def head(self, datasource: Datasource) -> QueryResult:
        resp = self._datasource_query(datasource, True, self.HEAD_QUERY_SIZE)
        return QueryResult.from_gql_query(resp, datasource)

    def get_datapoints(self, datasource: Datasource) -> QueryResult:
        return self._get_all(datasource, True)

    def _get_all(self, datasource: Datasource, include_metadata: bool) -> QueryResult:
        has_next_page = True
        after = None
        res = QueryResult([], datasource)
        while has_next_page:
            resp = self._datasource_query(datasource, include_metadata, self.FULL_LIST_PAGE_SIZE, after)
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

    def _datasource_query(self, datasource: Datasource, include_metadata: bool, limit: Optional[int] = None,
                          after: Optional[str] = None):
        q = GqlQueries.datasource_query(include_metadata)

        params = GqlQueries.datasource_query_params(
            datasource_id=datasource.source.id,
            query_input=datasource.serialize_gql_query_input(),
            first=limit,
            after=after
        )

        return self._exec(q, params)["datasourceQuery"]

    def update_metadata(self, datasource: Datasource, entries: List[DatapointMetadataUpdateEntry]):
        q = GqlMutations.update_metadata()

        assert datasource.source.id is not None
        assert len(entries) > 0

        params = GqlMutations.update_metadata_params(
            datasource_id=datasource.source.id,
            datapoints=[e.to_dict() for e in entries]
        )

        return self._exec(q, params)

    def get_datasources(self, id: Optional[str], name: Optional[str]) -> List[DatasourceResult]:
        q = GqlQueries.datasource()
        params = GqlQueries.datasource_params(id=id, name=name)

        res = self._exec(q, params)["datasource"]
        if res is None:
            return []
        return [dacite.from_dict(DatasourceResult, val, config=_dacite_config)
                for val in res]

    def delete_datasource(self, datasource: Datasource):
        q = GqlMutations.delete_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.delete_datasource_params(datasource_id=datasource.source.id)
        return self._exec(q, params)

    def rescan_datasource(self, datasource: Datasource):
        q = GqlMutations.rescan_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.rescan_datasource_params(datasource_id=datasource.source.id)
        return self._exec(q, params)
