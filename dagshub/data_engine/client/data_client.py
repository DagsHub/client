import logging
from typing import Any, Optional, List, Dict, Union, TYPE_CHECKING

import dacite
import gql
import rich.progress
from gql.transport.requests import RequestsHTTPTransport

import dagshub.auth
import dagshub.common.config
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.common.analytics import send_analytics_event
from dagshub.common.rich_util import get_rich_progress
from dagshub.data_engine.client.models import DatasourceResult, DatasourceType, IntegrationStatus, \
    PreprocessingStatus, DatasetResult, MetadataFieldType
from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.gql_queries import GqlQueries
from dagshub.data_engine.model.datasource import Datasource, DatapointMetadataUpdateEntry
from dagshub.data_engine.model.query_result import QueryResult

if TYPE_CHECKING:
    from dagshub.data_engine.datasources import DatasourceState

logger = logging.getLogger(__name__)

dacite_config = dacite.Config(cast=[IntegrationStatus, DatasourceType, PreprocessingStatus, MetadataFieldType])


class DataClient:
    HEAD_QUERY_SIZE = 100
    FULL_LIST_PAGE_SIZE = 5000

    def __init__(self, repo: str):
        # TODO: add project authentication here
        self.repo = repo
        self.host = config.host
        self.client = self._init_client()

    def _init_client(self):
        url = f"{self.host}/api/v1/repos/{self.repo}/data-engine/graphql"
        auth = HTTPBearerAuth(config.token or dagshub.auth.get_token(host=self.host))
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
        return dacite.from_dict(DatasourceResult, res["createDatasource"], config=dacite_config)

    def head(self, datasource: Datasource, size: Optional[int] = None) -> QueryResult:
        if size is None:
            size = self.HEAD_QUERY_SIZE

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task("Downloading metadata...", total=size)

        with progress:
            resp = self._datasource_query(datasource, True, size)
            progress.update(total_task, advance=size, refresh=True)

        return QueryResult.from_gql_query(resp, datasource)

    def sample(self, datasource: Datasource, n: Optional[int], include_metadata: bool) -> QueryResult:
        if n is None:
            return self._get_all(datasource, include_metadata)

        has_next_page = True
        after = None
        res = QueryResult([], datasource)
        left = n

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task("Downloading metadata...", total=left)

        with progress:
            while has_next_page and left > 0:
                take = min(left, self.FULL_LIST_PAGE_SIZE)
                resp = self._datasource_query(datasource, include_metadata, take, after)
                has_next_page = resp["pageInfo"]["hasNextPage"]
                after = resp["pageInfo"]["endCursor"]
                new_entries = QueryResult.from_gql_query(resp, datasource)
                res.entries += new_entries.entries
                left -= take
                progress.update(total_task, advance=len(res.entries), refresh=True)
        return res

    def get_datapoints(self, datasource: Datasource) -> QueryResult:
        return self._get_all(datasource, True)

    def _get_all(self, datasource: Datasource, include_metadata: bool) -> QueryResult:
        has_next_page = True
        after = None
        res = QueryResult([], datasource)
        # TODO: smarter batch sizing. Query a constant size at first
        #       On next queries adjust depending on the amount of metadata columns

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task("Downloading metadata...", total=None)

        with progress:
            while has_next_page:
                resp = self._datasource_query(datasource, include_metadata, self.FULL_LIST_PAGE_SIZE, after)
                has_next_page = resp["pageInfo"]["hasNextPage"]
                after = resp["pageInfo"]["endCursor"]

                new_entries = QueryResult.from_gql_query(resp, datasource)
                res.entries += new_entries.entries
                progress.update(total_task, advance=len(new_entries.entries), refresh=True)
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

        send_analytics_event("Client_DataEngine_QueryRun", repo=datasource.source.repoApi)

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
        return [dacite.from_dict(DatasourceResult, val, config=dacite_config)
                for val in res]

    def delete_datasource(self, datasource: Datasource):
        q = GqlMutations.delete_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.delete_datasource_params(datasource_id=datasource.source.id)
        return self._exec(q, params)

    def scan_datasource(self, datasource: Datasource):
        q = GqlMutations.scan_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.scan_datasource_params(datasource_id=datasource.source.id)
        return self._exec(q, params)

    def save_dataset(self, datasource: Datasource, name: str):
        q = GqlMutations.save_dataset()

        assert name is not None

        params = GqlMutations.save_dataset_params(datasource_id=datasource.source.id,
                                                  name=name,
                                                  query_input=datasource.serialize_gql_query_input())
        return self._exec(q, params)

    def get_datasets(self, id: Optional[Union[str, int]], name: Optional[str]) -> List[DatasetResult]:
        q = GqlQueries.dataset()
        params = GqlQueries.dataset_params(id=id, name=name)

        res = self._exec(q, params)["dataset"]
        if res is None:
            return []

        return [dacite.from_dict(DatasetResult, val, config=dacite_config)
                for val in res]
