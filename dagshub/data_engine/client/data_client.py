import datetime
import logging
from typing import Any, Optional, List, Dict, Union, TYPE_CHECKING, Tuple

import dacite
import gql
import rich.progress
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport

import dagshub.auth
import dagshub.common.config
from dagshub.common import config
from dagshub.common.analytics import send_analytics_event
from dagshub.common.rich_util import get_rich_progress
from dagshub.data_engine.client.gql_introspections import GqlIntrospections, TypesIntrospection
from dagshub.data_engine.client.models import (
    DatasourceResult,
    DatasetResult,
    MetadataFieldSchema,
    DatapointHistoryResult,
)
from dagshub.data_engine.client.models import ScanOption
from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.gql_queries import GqlQueries
from dagshub.data_engine.client.query_builder import GqlQuery
from dagshub.data_engine.model.errors import DataEngineGqlError
from dagshub.data_engine.model.query_result import QueryResult


from dagshub.data_engine.model.schema_util import dacite_config

if TYPE_CHECKING:
    from dagshub.data_engine.datasources import DatasourceState
    from dagshub.data_engine.model.datasource import (
        Datasource,
        DatapointMetadataUpdateEntry,
        DatapointDeleteMetadataEntry,
        DatapointDeleteEntry,
    )
    from dagshub.data_engine.model.datapoint import Datapoint

logger = logging.getLogger(__name__)


class DataClient:
    HEAD_QUERY_SIZE = 100
    FULL_LIST_PAGE_SIZE = 5000
    DATAPOINT_HISTORY_PAGE_SIZE = 5000

    _known_introspections: Dict[str, TypesIntrospection] = {}
    """GraphQL schema for each host"""

    def __init__(self, repo: str):
        self.repo = repo
        self.host = config.host
        self.client = self._init_client()

    def _init_client(self):
        url = f"{self.host}/api/v1/repos/{self.repo}/data-engine/graphql"
        auth = dagshub.auth.get_authenticator(host=self.host)
        transport = RequestsHTTPTransport(url=url, auth=auth, headers=config.requests_headers)
        client = gql.Client(transport=transport)
        return client

    def create_datasource(self, ds: "DatasourceState") -> DatasourceResult:
        """
        Create a new datasource using the provided datasource state.

        Args:
            ds (DatasourceState): The datasource state containing information about the datasource.

        Returns:
            DatasourceResult: The result of creating the datasource.

        """
        q = GqlMutations.create_datasource()

        assert ds.name is not None
        assert ds.path is not None
        assert ds.source_type is not None

        params = GqlMutations.create_datasource_params(name=ds.name, url=ds.path, ds_type=ds.source_type)
        res = self._exec(q, params)
        return dacite.from_dict(DatasourceResult, res["createDatasource"], config=dacite_config)

    def head(self, datasource: "Datasource", size: Optional[int] = None) -> QueryResult:
        """
        Retrieve a subset of data from the datasource headers.

        Args:
            datasource (Datasource): The datasource to retrieve data from.
            size (Optional[int], optional): The number of entries to retrieve. Defaults to None.

        Returns:
            QueryResult: The query result containing the retrieved data.(By Default returns the first 100 samples)

        """
        if size is None:
            size = self.HEAD_QUERY_SIZE

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        total_task = progress.add_task("Downloading metadata...", total=size)

        with progress:
            resp = self._datasource_query(datasource, True, size)
            progress.update(total_task, advance=size, refresh=True)

        return QueryResult.from_gql_query(resp, datasource)

    def sample(self, datasource: "Datasource", n: Optional[int], include_metadata: bool) -> QueryResult:
        """
        Sample data from the datasource.

        Args:
            datasource (Datasource): The datasource to sample data from.
            n (Optional[int]): The number of data points to sample.
            include_metadata (bool): Whether to include metadata in the sampled data.

        Returns:
            QueryResult: The query result containing the sampled data.
        """
        if n is None:
            return self._get_all(datasource, include_metadata)

        has_next_page = True
        after = None
        res = QueryResult([], datasource, [])
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
                res.fields = new_entries.fields
                res.query_data_time = new_entries.query_data_time
                left -= take
                progress.update(total_task, advance=len(res.entries), refresh=True)
        return res

    def get_datapoints(self, datasource: "Datasource") -> QueryResult:
        return self._get_all(datasource, True)

    def _get_all(self, datasource: "Datasource", include_metadata: bool) -> QueryResult:
        has_next_page = True
        after = None
        res = QueryResult([], datasource, [])
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
                res.fields = new_entries.fields
                res.query_data_time = new_entries.query_data_time
                progress.update(total_task, advance=len(new_entries.entries), refresh=True)

        return res

    def _exec(
        self,
        query: GqlQuery,
        params: Optional[Dict[str, Any]] = None,
        validate=True,
    ) -> Dict[str, Any]:
        logger.debug(f"Executing query: {query}")
        if params is not None:
            logger.debug(f"Params: {params}")
        if validate:
            query.validate_params(params if params else {}, self.query_introspection)
        q = gql.gql(query.generate())
        try:
            resp = self.client.execute(q, variable_values=params)
        except TransportQueryError as e:
            raise DataEngineGqlError(e, self.client.transport.response_headers.get("X-DagsHub-Support-Id"))
        return resp

    def _datasource_query(
        self, datasource: "Datasource", include_metadata: bool, limit: Optional[int] = None, after: Optional[str] = None
    ):
        send_analytics_event("Client_DataEngine_QueryRun", repo=datasource.source.repoApi)

        q = GqlQueries.datasource_query(include_metadata, self.query_introspection)

        params = GqlQueries.datasource_query_params(
            datasource_id=datasource.source.id,
            query_input=datasource.serialize_gql_query_input(),
            first=limit,
            after=after,
        )
        return self._exec(q, params)["datasourceQuery"]

    @property
    def query_introspection(self) -> TypesIntrospection:
        if self.host not in self._known_introspections:
            introspection = GqlIntrospections.obj_fields()
            # Keep validate = False otherwise you get into an infinite loop
            introspection_dict = self._exec(introspection, validate=False)
            self._known_introspections[self.host] = dacite.from_dict(
                data_class=TypesIntrospection, data=introspection_dict["__schema"]
            )
        return self._known_introspections[self.host]

    def update_metadata(self, datasource: "Datasource", entries: List["DatapointMetadataUpdateEntry"]):
        """
        Update the Datasource with the metadata entry

        Args:
            datasource (Datasource): The datasource instance to be updated
            entries (List[DatapointMetadataUpdateEntry]): The new metadata entries

        Returns:
            Updates the Datasource.

        """
        q = GqlMutations.update_metadata()

        assert datasource.source.id is not None
        assert len(entries) > 0

        params = GqlMutations.update_metadata_params(
            datasource_id=datasource.source.id, datapoints=[e.to_dict() for e in entries]
        )
        return self._exec(q, params)

    def delete_metadata_for_datapoint(self, datasource: "Datasource", entries: List["DatapointDeleteMetadataEntry"]):
        """
        Delete a metadata from a datapoint

        Args:
            datasource (Datasource): The datasource instance to be updated
            entries (List[DatapointDeleteMetadataEntry]): The metadata entries to delete

        Returns:
            Updates the Datasource.

        """
        q = GqlMutations.delete_metadata_for_datapoint()

        assert datasource.source.id is not None
        assert len(entries) > 0

        params = GqlMutations.delete_metadata_params(
            datasource_id=datasource.source.id, datapoints=[e.to_dict() for e in entries]
        )
        return self._exec(q, params)

    def delete_datapoints(self, datasource: "Datasource", entries: List["DatapointDeleteEntry"]):
        """
        Delete a datapoints from the datasource.

        Args:
            datasource (Datasource): The datasource instance to be updated
            entries: the list of the datapoints to delete

        """
        q = GqlMutations.delete_datapoints()

        assert datasource.source.id is not None
        assert len(entries) > 0

        params = GqlMutations.delete_datapoints_params(
            datasource_id=datasource.source.id, datapoints=[e.to_dict() for e in entries]
        )
        return self._exec(q, params)

    def update_metadata_fields(self, datasource: "Datasource", metadata_field_props: List[MetadataFieldSchema]):
        q = GqlMutations.update_metadata_field()

        assert datasource.source.id is not None

        params = GqlMutations.update_metadata_fields_params(
            datasource_id=datasource.source.id, metadata_field_props=[e.to_dict() for e in metadata_field_props]
        )

        return self._exec(q, params)

    def get_datasources(self, id: Optional[str], name: Optional[str]) -> List[DatasourceResult]:
        """
        Retrieve a list of datasources based on optional filtering criteria.

        Args:
            id (Optional[str]): Optional datasource ID to filter by.
            name (Optional[str]): Optional datasource name to filter by.

        Returns:
            List[DatasourceResult]: A list of datasources that match the filtering criteria.
        """
        q = GqlQueries.datasource()
        params = GqlQueries.datasource_params(id=id, name=name)

        res = self._exec(q, params)["datasource"]
        if res is None:
            return []
        return [dacite.from_dict(DatasourceResult, val, config=dacite_config) for val in res]

    def delete_datasource(self, datasource: "Datasource"):
        """
        Delete a specified datasource.
         Args:
            datasource (Datasource): The datasource instance to be deleted.
        """
        q = GqlMutations.delete_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.delete_datasource_params(datasource_id=datasource.source.id)
        return self._exec(q, params)

    def scan_datasource(self, datasource: "Datasource", options: Optional[List[ScanOption]]):
        """
        Initiate a scan operation on the specified datasource.

         Args:
            datasource (Datasource): The datasource instance to be updated
        """
        q = GqlMutations.scan_datasource()

        assert datasource.source.id is not None

        params = GqlMutations.scan_datasource_params(datasource_id=datasource.source.id, options=options)
        return self._exec(q, params)

    def save_dataset(self, datasource: "Datasource", name: str):
        """
        Save a dataset using the specified datasource and name.

        Args:
            datasource (Datasource): The datasource instance to be saved.
            name (str) : Name of the new datasource instance

        Example:
            For a detailed description of how to create and save datasets, refer to this link:
                "https://dagshub.com/docs/use_cases/data_engine/query_and_create_subsets/#querying-and-saving-subsets-of-your-data
        """
        q = GqlMutations.save_dataset()

        assert name is not None

        params = GqlMutations.save_dataset_params(
            datasource_id=datasource.source.id, name=name, query_input=datasource.serialize_gql_query_input()
        )
        return self._exec(q, params)

    def delete_dataset(self, dataset_id: Union[str, int]):
        """
        Removes a dataset. This doesn't remove the underlying source.
        """
        q = GqlMutations.delete_dataset()

        assert dataset_id is not None

        params = GqlMutations.delete_dataset_params(dataset_id=dataset_id)
        return self._exec(q, params)

    def get_datasets(self, id: Optional[Union[str, int]], name: Optional[str]) -> List[DatasetResult]:
        """
        Retrieve a list of datasets based on optional filtering criteria.

        Args:
            id (Optional[Union[str, int]): Optional dataset ID or name to filter by.
            name (Optional[str]): Optional dataset name to filter by.

        Returns:
            List[DatasetResult]: A list of datasets that match the filtering criteria.
        """
        q = GqlQueries.dataset()
        params = GqlQueries.dataset_params(id=id, name=name)

        res = self._exec(q, params)["dataset"]
        if res is None:
            return []

        return [dacite.from_dict(DatasetResult, val, config=dacite_config) for val in res]

    def get_datapoint_history(
        self,
        datapoints: List["Datapoint"],
        fields: Optional[List[str]],
        from_time: Optional[datetime.datetime],
        to_time: Optional[datetime.datetime],
    ) -> Dict[str, List[DatapointHistoryResult]]:
        ds_id = datapoints[0].datasource.source.id
        assert ds_id is not None
        assert len(datapoints) > 0

        after = None
        hasNextPage = True

        q = GqlQueries.datapoint_history()

        res: Dict[str, List[DatapointHistoryResult]] = {}

        while hasNextPage:
            params = GqlQueries.datapoint_history_params(
                ds_id,
                [dp.path for dp in datapoints],
                fields,
                from_time,
                to_time,
                after,
                self.DATAPOINT_HISTORY_PAGE_SIZE,
            )
            page, after = self._get_datapoint_history(q, params)
            hasNextPage = after is not None
            for dp_path, history in page.items():
                if dp_path not in res:
                    res[dp_path] = []
                res[dp_path].extend(history)

        return res

    def _get_datapoint_history(
        self,
        query: GqlQuery,
        params: Dict[str, Any],
    ) -> Tuple[Dict[str, List[DatapointHistoryResult]], Optional[str]]:
        queryRes = self._exec(query, params)["datapointHistory"]
        if queryRes is None or queryRes.get("edges") is None:
            return {}, None

        res: Dict[str, List[DatapointHistoryResult]] = {}
        for val in queryRes["edges"]:
            dpPath = val["node"]["path"]
            history = [
                dacite.from_dict(DatapointHistoryResult, v, config=dacite_config) for v in val["node"]["history"]
            ]
            res[dpPath] = history

        cursor = queryRes["pageInfo"]["endCursor"]
        hasNextPage = queryRes["pageInfo"]["hasNextPage"]

        cursor = cursor if hasNextPage else None

        return res, cursor
