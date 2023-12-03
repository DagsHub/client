import base64
import gzip
import json
import logging
import math
import os.path
import time
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, Set, ContextManager

import rich.progress
from dataclasses_json import dataclass_json, config
from pathvalidate import sanitize_filepath

import dagshub.common.config
from dagshub.common import rich_console
from dagshub.common.analytics import send_analytics_event
from dagshub.common.helpers import prompt_user, http_request, log_message
from dagshub.common.rich_util import get_rich_progress
from dagshub.common.util import lazy_load, multi_urljoin
from dagshub.data_engine.client.models import (
    PreprocessingStatus,
    MetadataFieldSchema,
    ScanOption,
    autogenerated_columns,
)
from dagshub.data_engine.dtypes import MetadataFieldType
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.errors import (
    WrongOperatorError,
    WrongOrderError,
    DatasetFieldComparisonError,
    FieldNotFoundError,
)
from dagshub.data_engine.model.metadata_field_builder import MetadataFieldBuilder
from dagshub.data_engine.model.query import DatasourceQuery
from dagshub.data_engine.model.schema_util import metadataTypeLookup, metadataTypeLookupReverse

if TYPE_CHECKING:
    from dagshub.data_engine.model.query_result import QueryResult
    from dagshub.data_engine.model.datasource_state import DatasourceState
    import fiftyone as fo
    import pandas
else:
    plugin_server_module = lazy_load("dagshub.data_engine.voxel_plugin_server.server")
    fo = lazy_load("fiftyone")

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class DatapointMetadataUpdateEntry(json.JSONEncoder):
    url: str
    key: str
    value: str
    valueType: MetadataFieldType = field(metadata=config(encoder=lambda val: val.value))
    allowMultiple: bool = False


class Datasource:
    def __init__(self, datasource: "DatasourceState", query: Optional[DatasourceQuery] = None):
        self._source = datasource
        if query is None:
            query = DatasourceQuery()
        self._query = query

        self.serialize_gql_query_input()

    @property
    def source(self) -> "DatasourceState":
        return self._source

    def clear_query(self):
        """
        Clear the attached query. Next time this datasource gets queried, you'll get all of the datapoints.

        .. note::
            This function always clears the query.
            That means that if you use it on a dataset, the whole query will get cleared, and not just your changes.
        """
        self._query = DatasourceQuery()

    def __deepcopy__(self, memodict={}) -> "Datasource":
        res = Datasource(self._source, self._query.__deepcopy__())
        return res

    def get_query(self):
        return self._query

    @property
    def annotation_fields(self) -> List[str]:
        """Return all fields that have the annotation meta tag set"""
        return [f.name for f in self.fields if f.is_annotation()]

    def serialize_gql_query_input(self):
        return {
            "query": self._query.serialize_graphql(),
        }

    def sample(self, start: Optional[int] = None, end: Optional[int] = None):
        if start is not None:
            logger.warning("Starting slices is not implemented for now")
        return self._source.client.sample(self, end, include_metadata=True)

    def head(self, size=100) -> "QueryResult":
        """
        Executes the query and returns a :class:`.QueryResult` object containing first ``size`` datapoints

        Args:
            size: how many datapoints to get. Default is 100
        """
        self._check_preprocess()
        send_analytics_event("Client_DataEngine_DisplayTopResults", repo=self.source.repoApi)
        return self._source.client.head(self, size)

    def all(self) -> "QueryResult":
        """
        Executes the query and returns a :class:`.QueryResult` object containing all datapoints
        """
        self._check_preprocess()
        return self._source.client.get_datapoints(self)

    def _check_preprocess(self):
        self.source.get_from_dagshub()
        if (
            self.source.preprocessing_status == PreprocessingStatus.IN_PROGRESS
            or self.source.preprocessing_status == PreprocessingStatus.AUTO_SCAN_IN_PROGRESS
        ):
            logger.warning(
                f"Datasource {self.source.name} is currently in the progress of rescanning. "
                f"Values might change if you requery later"
            )

    def metadata_field(self, field_name: str) -> MetadataFieldBuilder:
        """
        Returns a builder for a metadata field.
        The builder can be used to change properties of a field or create a new field altogether.
        Note that fields get automatically created when you upload new metadata to the Data Engine,
        so it's not necessary to create fields with this function.

        Example of creating a new annotation field::

            ds.metadata_field("annotation").set_type(dtypes.LabelStudioAnnotation).apply()

        .. note::
            New fields have to have their type defined using .set_type() before doing anything else

        Example of marking an existing field as an annotation field::

            ds.metadata_field("existing-field").set_annotation().apply()

        Args:
            field_name: Name of the field that you want to create/change

        """
        return MetadataFieldBuilder(self, field_name)

    def apply_field_changes(self, field_builders: List[MetadataFieldBuilder]):
        """
        Applies one or multiple metadata field builders
        that can be constructed using the :func:`metadata_field()` function.
        """
        self.source.client.update_metadata_fields(self, [builder.schema for builder in field_builders])
        self.source.get_from_dagshub()

    def metadata_context(self) -> ContextManager["MetadataContextManager"]:
        """
        Returns a metadata context, that you can upload metadata through using its
        :func:`~MetadataContextManager.update_metadata()` function.
        Once the context is exited, all metadata is uploaded in one batch::

            with df.metadata_context() as ctx:
                ctx.update_metadata("file1", {"key1": True, "key2": "value"})

        """

        # Need to have the context manager inside a wrapper to satisfy MyPy + PyCharm type hinter
        @contextmanager
        def func():
            self.source.get_from_dagshub()
            send_analytics_event("Client_DataEngine_addEnrichments", repo=self.source.repoApi)
            ctx = MetadataContextManager(self)
            yield ctx
            self._upload_metadata(ctx.get_metadata_entries())

        return func()

    def upload_metadata_from_dataframe(self, df: "pandas.DataFrame", path_column: Optional[Union[str, int]] = None):
        """
        Upload metadata from a pandas dataframe.

        All columns are uploaded as metadata, and the path of every datapoint is taken from `path_column`.

        Args:
            df (`pandas.DataFrame <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_):
                DataFrame with metadata
            path_column: Column with the datapoints' paths. Can either be the name of the column, or its index.
                If not specified, the first column is used.
        """
        self.source.get_from_dagshub()
        send_analytics_event("Client_DataEngine_addEnrichmentsWithDataFrame", repo=self.source.repoApi)
        self._upload_metadata(self._df_to_metadata(df, path_column, multivalue_fields=self._get_multivalue_fields()))

    def _get_multivalue_fields(self) -> Set[str]:
        res = set()
        for col in self.source.metadata_fields:
            if col.multiple:
                res.add(col.name)
        return res

    def _df_to_metadata(
        self, df: "pandas.DataFrame", path_column: Optional[Union[str, int]] = None, multivalue_fields=set()
    ) -> List[DatapointMetadataUpdateEntry]:
        res: List[DatapointMetadataUpdateEntry] = []
        if path_column is None:
            path_column = df.columns[0]
        elif type(path_column) is str:
            if path_column not in df.columns:
                raise RuntimeError(f"Column {path_column} does not exist in the dataframe")
        elif type(path_column) is int:
            path_column = df.columns[path_column]

        # objects are actually mixed and not guaranteed to be string, but this should cover most use cases
        if df.dtypes[path_column] != "object":
            raise RuntimeError(f"Column {path_column} doesn't have strings")

        field_value_types = {f.name: f.valueType for f in self.fields}

        for _, row in df.iterrows():
            datapoint = row[path_column]
            for key, val in row.items():
                if key == path_column:
                    continue
                key = str(key)
                if key in autogenerated_columns:
                    continue
                if val is None:
                    continue
                # ONLY FOR PANDAS: since pandas doesn't distinguish between None and NaN, don't upload it
                if type(val) is float and math.isnan(val):
                    continue
                if type(val) is list:
                    if key not in multivalue_fields:
                        multivalue_fields.add(key)
                        # Promote all the existing uploading metadata to multivalue
                        for update_entry in res:
                            if update_entry.key == key:
                                update_entry.allowMultiple = True
                    for sub_val in val:
                        value_type = field_value_types.get(key)
                        if value_type is None:
                            value_type = metadataTypeLookup[type(sub_val)]
                            field_value_types[key] = value_type
                        # Don't override bytes if they're not bytes - probably just undownloaded values
                        if value_type == MetadataFieldType.BLOB and type(sub_val) is not bytes:
                            continue
                        # Pandas quirk - integers are floats on the backend
                        if value_type == MetadataFieldType.INTEGER:
                            sub_val = int(sub_val)
                        if type(sub_val) is bytes:
                            sub_val = MetadataContextManager.wrap_bytes(sub_val)
                        res.append(
                            DatapointMetadataUpdateEntry(
                                url=datapoint, key=key, value=str(sub_val), valueType=value_type, allowMultiple=True
                            )
                        )
                else:
                    value_type = field_value_types.get(key)
                    if value_type is None:
                        value_type = metadataTypeLookup[type(val)]
                        field_value_types[key] = value_type
                    # Don't override bytes if they're not bytes - probably just undownloaded values
                    if value_type == MetadataFieldType.BLOB and type(val) is not bytes:
                        continue
                    # Pandas quirk - integers are floats on the backend
                    if value_type == MetadataFieldType.INTEGER:
                        val = int(val)
                    if type(val) is bytes:
                        val = MetadataContextManager.wrap_bytes(val)
                    res.append(
                        DatapointMetadataUpdateEntry(
                            url=datapoint,
                            key=key,
                            value=str(val),
                            valueType=value_type,
                            allowMultiple=key in multivalue_fields,
                        )
                    )
        return res

    def delete_source(self, force: bool = False):
        """
        Delete the record of this datasource along with all datapoints.

        .. warning::
            This is a destructive operation! If you delete the datasource,
            all the datapoints and metadata will be removed.

        Args:
            force: Skip the confirmation prompt
        """
        prompt = (
            f'You are about to delete datasource "{self.source.name}" for repo "{self.source.repo}"\n'
            f"This will remove the datasource and ALL datapoints "
            f"and metadata records associated with the source."
        )
        if not force:
            user_response = prompt_user(prompt)
            if not user_response:
                print("Deletion cancelled")
                return
        self.source.client.delete_datasource(self)

    def scan_source(self, options: Optional[List[ScanOption]] = None):
        """
        This function fires a call to the backend to rescan the datapoints.
        Call this function whenever you uploaded new files and want them to appear when querying the datasource,
        or if you changed existing file contents and want their metadata to be updated.

        DagsHub periodically rescans all datasources, this function is a way to make a scan happen as soon as possible.

        Notes about automatically scanned metadata:
            1. Only new datapoints (files) will be added.
               If files were removed from the source, their metadata will still remain,
               and they will still be returned from queries on the datasource.
               An API to actively remove metadata will be available soon.
            2. Some metadata fields will be automatically scanned and updated by DagsHub based on this scan -
               the list of automatic metadata fields is growing frequently!

        Args:
            options: List of scanning options. If not sure, leave empty.
        """
        logger.debug("Rescanning datasource")
        self.source.client.scan_datasource(self, options=options)

    def _upload_metadata(self, metadata_entries: List[DatapointMetadataUpdateEntry]):
        progress = get_rich_progress(rich.progress.MofNCompleteColumn())

        upload_batch_size = dagshub.common.config.dataengine_metadata_upload_batch_size
        total_entries = len(metadata_entries)
        total_task = progress.add_task(f"Uploading metadata (batch size {upload_batch_size})...", total=total_entries)

        with progress:
            for start in range(0, total_entries, upload_batch_size):
                entries = metadata_entries[start : start + upload_batch_size]
                logger.debug(f"Uploading {len(entries)} metadata entries...")
                self.source.client.update_metadata(self, entries)
                progress.update(total_task, advance=upload_batch_size)
            progress.update(total_task, completed=total_entries, refresh=True)

        # Update the status from dagshub, so we get back the new metadata columns
        self.source.get_from_dagshub()

    def save_dataset(self, name: str):
        """
        Save the dataset, which is a combination of datasource + query, on the backend.
        That way you can persist and share your queries.
        You can get the dataset back by calling :func:`.datasets.get_dataset()`

        Args:
            name: Name of the dataset
        """
        send_analytics_event("Client_DataEngine_QuerySaved", repo=self.source.repoApi)

        self.source.client.save_dataset(self, name)
        log_message(f"Dataset {name} saved")

    def to_voxel51_dataset(self, **kwargs) -> "fo.Dataset":
        """
        Refer to :func:`QueryResult.to_voxel51_dataset() \
        <dagshub.data_engine.model.query_result.QueryResult.to_voxel51_dataset>`\
        for documentation.
        """
        return self.all().to_voxel51_dataset(**kwargs)

    @property
    def default_dataset_location(self) -> Path:
        """
        Default location where datapoint files are stored.

        On UNIX-likes the path is ``~/dagshub/datasets/<repo_name>/<datasource_id>``

        On Windows the path is ``C:\\Users\\<user>\\dagshub\\datasets\\<repo_name>\\<datasource_id>``
        """
        return Path(
            sanitize_filepath(os.path.join(Path.home(), "dagshub", "datasets", self.source.repo, str(self.source.id)))
        )

    def visualize(self, **kwargs) -> "fo.Session":
        """
        Visualize the whole datasource using
        :func:`QueryResult.visualize() <dagshub.data_engine.model.query_result.QueryResult.visualize>`.

        Read the function docs for kwarg documentation.
        """
        return self.all().visualize(**kwargs)

    @property
    def fields(self) -> List[MetadataFieldSchema]:
        return self.source.metadata_fields

    def annotate(self) -> Optional[str]:
        """
        Sends all datapoints in the datasource for annotation in Label Studio.

        .. note::
            This will send ALL datapoints in the datasource for annotation.
            It's recommended to not send a huge amount of datapoints to be annotated at once, to avoid overloading
            the Label Studio workspace.
            Use :func:`QueryResult.annotate() <dagshub.data_engine.model.query_result.QueryResult.annotate>`
            to annotate a result of a query with less datapoints.
            Alternatively, use a lower level :func:`send_datapoints_to_annotation` function


        :return: Link to open Label Studio in the browser
        """
        return self.all().annotate()

    def send_to_annotation(self):
        """
        deprecated, see :func:`annotate()`

        :meta private:
        """
        return self.annotate()

    def send_datapoints_to_annotation(
        self, datapoints: Union[List[Datapoint], "QueryResult", List[Dict]], open_project=True, ignore_warning=False
    ) -> Optional[str]:
        """
        Sends datapoints for annotation in Label Studio.

        Args:
            datapoints: Either of:

                - A :class:`.QueryResult`
                - List of :class:`.Datapoint` objects
                - List of dictionaries. Each dictionary should have fields ``id`` and ``download_url``.
                    ``id`` is the ID of the datapoint in the datasource.

            open_project: Automatically open the created Label Studio project in the browser.
            ignore_warning: Suppress the prompt-warning if you try to annotate too many datapoints at once.

        Returns:
            Link to open Label Studio in the browser
        """

        if len(datapoints) == 0:
            logger.warning("No datapoints provided to be sent to annotation")
            return None
        elif len(datapoints) > dagshub.common.config.recommended_annotate_limit and not ignore_warning:
            force = prompt_user(
                f"You are attempting to annotate {len(datapoints)} datapoints at once - it's "
                f"recommended to only annotate up to "
                f"{dagshub.common.config.recommended_annotate_limit} "
                f"datapoints at a time."
            )
            if not force:
                return ""

        req_data = {"datasource_id": self.source.id, "datapoints": []}

        for dp in datapoints:
            req_dict = {}
            if type(dp) is dict:
                req_dict["id"] = dp["datapoint_id"]
                req_dict["download_url"] = dp["download_url"]
            else:
                req_dict["id"] = dp.datapoint_id
                req_dict["download_url"] = dp.download_url
            req_data["datapoints"].append(req_dict)

        init_url = multi_urljoin(self.source.repoApi.data_engine_url, "annotations/init")
        resp = http_request("POST", init_url, json=req_data, auth=self.source.repoApi.auth)

        if resp.status_code != 200:
            logger.error(f"Error while sending request for annotation: {resp.content}")
            return None
        link = resp.json()["link"]

        # Do a raw print so it works in colab/jupyter
        print("Open the following link to start working on your annotation project:")
        print(link)

        if open_project:
            webbrowser.open_new_tab(link)
        return link

    def _launch_annotation_workspace(self):
        try:
            start_workspace_url = multi_urljoin(self.source.repoApi.annotations_url, "start")
            http_request("POST", start_workspace_url, auth=self.source.repoApi.auth)
        except:  # noqa
            pass

    def wait_until_ready(self, max_wait_time=300, fail_on_timeout=True):
        """
        Blocks until the datasource preprocessing is complete.

        Useful when you have just created a datasource and the initial scanning hasn't finished yet.

        Args:
            max_wait_time: Maximum time to wait in seconds
            fail_on_timeout: Whether to raise a RuntimeError or log a warning if the scan does not complete on time
        """

        # Start LS workspace to save time later in the flow
        self._launch_annotation_workspace()

        start = time.time()
        if max_wait_time:
            rich_console.log(f"Maximum waiting time set to {int(max_wait_time / 60)} minutes")
        spinner = rich_console.status("Waiting for datasource preprocessing to complete...")
        with spinner:
            while True:
                self.source.get_from_dagshub()
                if self.source.preprocessing_status == PreprocessingStatus.READY:
                    return

                if self.source.preprocessing_status == PreprocessingStatus.FAILED:
                    raise RuntimeError("Datasource preprocessing failed")

                if max_wait_time is not None and (time.time() - start) > max_wait_time:
                    if fail_on_timeout:
                        raise RuntimeError(
                            f"Time limit of {max_wait_time} seconds reached before processing was completed."
                        )
                    else:
                        logger.warning(
                            f"Time limit of {max_wait_time} seconds reached before processing was completed."
                        )
                        return

                time.sleep(1)

    def has_field(self, field_name: str) -> bool:
        """
        Checks if a metadata field ``field_name`` exists in the datasource.
        """
        reserved_searchable_fields = ["path"]
        fields = (f.name for f in self.fields)
        return field_name in reserved_searchable_fields or field_name in fields

    def __repr__(self):
        res = f"Datasource {self.source.name}"
        res += f"\n\tRepo: {self.source.repo}, path: {self.source.path}"
        res += f"\n\t{self._query}"
        res += "\n\tFields:"
        for f in self.fields:
            res += f"\n\t\t{f}"
        return res + "\n"

    """ FUNCTIONS RELATED TO QUERYING
    These are functions that overload operators on the DataSet, so you can do pandas-like filtering
        ds = Dataset(...)
        queried_ds = ds[ds["value"] == 5]
    """

    def __getitem__(self, other: Union[slice, str, "Datasource"]):
        # Slicing - get items from the slice
        if type(other) is slice:
            return self.sample(other.start, other.stop)

        # Otherwise we're doing querying
        new_ds = self.__deepcopy__()
        if type(other) is str:
            if not self.has_field(other):
                raise FieldNotFoundError(other)
            other_query = DatasourceQuery(other)
            if self._query.is_empty:
                new_ds._query = other_query
            else:
                new_ds._query.compose("and", other_query)
            return new_ds
        # "index" is a datasource with a query - return the datasource inside
        # Example:
        #   ds = Dataset()
        #   filtered_ds = ds[ds["aaa"] > 5]
        #   filtered_ds2 = filtered_ds[filtered_ds["bbb"] < 4]
        # filtered_ds2 will be "aaa" > 5 AND "bbb" < 4
        if isinstance(other, Datasource):
            return other

    def __gt__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("gt", other)

    def __ge__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("ge", other)

    def __le__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("le", other)

    def __lt__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("lt", other)

    def __eq__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if other is None:
            return self.is_null()
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("eq", other)

    def __ne__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if other is None:
            return self.is_not_null()
        if not isinstance(other, (int, float, str)):
            raise NotImplementedError
        return self.add_query_op("eq", other).add_query_op("not")

    def __invert__(self):
        return self.add_query_op("not")

    def __contains__(self, item):
        raise WrongOperatorError("Use `ds.contains(a)` for querying instead of `a in ds`")

    def contains(self, item: str):
        """
        Check if the filtering field contains the specified string item.

        :meta private:
        """
        if type(item) is not str:
            return WrongOperatorError(f"Cannot use contains with non-string value {item}")
        self._test_not_comparing_other_ds(item)
        return self.add_query_op("contains", item)

    def is_null(self):
        """
        Check if the filtering field is null.

        :meta private:
        """
        field = self._get_filtering_field()
        value_type = metadataTypeLookupReverse[field.valueType.value]
        return self.add_query_op("isnull", value_type())

    def is_not_null(self):
        """
        Check if the filtering field is not null.

        :meta private:
        """
        return self.is_null().add_query_op("not")

    def _get_filtering_field(self) -> MetadataFieldSchema:
        field_name = self.get_query().column_filter
        if field_name is None:
            raise RuntimeError("The current query filter is not a field")
        for col in self.source.metadata_fields:
            if col.name == field_name:
                return col
        raise RuntimeError(f"Field {field_name} doesn't exist in the current uploaded metadata")

    def __and__(self, other: "Datasource"):
        return self.add_query_op("and", other)

    def __or__(self, other: "Datasource"):
        return self.add_query_op("or", other)

    # Prevent users from messing up their queries due to operator order
    # They always need to put the dataset query filters in parentheses, otherwise the binary and/or get executed before
    def __rand__(self, other):
        if type(other) is not Datasource:
            raise WrongOrderError(type(other))
        raise NotImplementedError

    def __ror__(self, other):
        if type(other) is not Datasource:
            raise WrongOrderError(type(other))
        raise NotImplementedError

    def add_query_op(
        self, op: str, other: Optional[Union[str, int, float, "Datasource", "DatasourceQuery"]] = None
    ) -> "Datasource":
        """
        Add a query operation to the current Datasource instance.

        Args:
            op (str): The operation to be performed in the query.
            other (Optional[Union[str, int, float, "Datasource", "DatasourceQuery"]], optional):
                The operand for the query operation. Defaults to None.

        Returns:
            Datasource: A new Datasource instance with the added query operation.

        :meta private:
        """
        new_ds = self.__deepcopy__()
        if type(other) is Datasource:
            other = other.get_query()
        new_ds._query.compose(op, other)
        return new_ds

    @staticmethod
    def _test_not_comparing_other_ds(other):
        if type(other) is Datasource:
            raise DatasetFieldComparisonError()


class MetadataContextManager:
    """
    Context manager for updating the metadata on a datasource.
    Batches the metadata changes, so they are being sent all at once.
    """

    def __init__(self, datasource: Datasource):
        self._datasource = datasource
        self._metadata_entries: List[DatapointMetadataUpdateEntry] = []
        self._multivalue_fields = datasource._get_multivalue_fields()

    def update_metadata(self, datapoints: Union[List[str], str], metadata: Dict[str, Any]):
        """
        Update metadata for the specified datapoints.

        .. note::
            If ``datapoints`` is a list, the same metadata is assigned to all the datapoints in the list.
            Call ``update_metadata()`` separately for each datapoint if you need to assign different metadata.

        Args:
            datapoints (Union[List[str], str]): A list of datapoints or a single datapoint path to update metadata for.
            metadata (Dict[str, Any]): A dictionary containing metadata key-value pairs to update.

        Example::

            with ds.metadata_context() as ctx:
                metadata = {
                    "episode": 5,
                    "has_baby_yoda": True,
                }

                # Attach metadata to a single specific file in the datasource.
                # The first argument is the filepath to attach metadata to, **relative to the root of the datasource**.
                ctx.update_metadata("images/005.jpg", metadata)

                # Attach metadata to several files at once:
                ctx.update_metadata(["images/006.jpg","images/007.jpg"], metadata)

        """
        if isinstance(datapoints, str):
            datapoints = [datapoints]

        field_value_types = {f.name: f.valueType for f in self._datasource.fields}

        for dp in datapoints:
            for k, v in metadata.items():
                if v is None:
                    continue
                if k in autogenerated_columns:
                    continue

                if type(v) is list:
                    if k not in self._multivalue_fields:
                        self._multivalue_fields.add(k)
                        # Promote all existing ones to multivalue
                        for e in self._metadata_entries:
                            if e.key == k:
                                e.allowMultiple = True
                    for sub_val in v:
                        value_type = field_value_types.get(k)
                        if value_type is None:
                            value_type = metadataTypeLookup[type(sub_val)]
                            field_value_types[k] = value_type
                        # Don't override bytes if they're not bytes - probably just undownloaded values
                        if value_type == MetadataFieldType.BLOB and type(sub_val) is not bytes:
                            continue

                        if type(v) is bytes:
                            sub_val = self.wrap_bytes(sub_val)
                        self._metadata_entries.append(
                            DatapointMetadataUpdateEntry(
                                url=dp,
                                key=k,
                                value=str(sub_val),
                                # todo: preliminary type check
                                valueType=value_type,
                                allowMultiple=k in self._multivalue_fields,
                            )
                        )

                else:
                    value_type = field_value_types.get(k)
                    if value_type is None:
                        value_type = metadataTypeLookup[type(v)]
                        field_value_types[k] = value_type
                    # Don't override bytes if they're not bytes - probably just undownloaded values
                    if value_type == MetadataFieldType.BLOB and type(v) is not bytes:
                        continue

                    if type(v) is bytes:
                        v = self.wrap_bytes(v)

                    self._metadata_entries.append(
                        DatapointMetadataUpdateEntry(
                            url=dp,
                            key=k,
                            value=str(v),
                            valueType=value_type,
                            # todo: preliminary type check
                            allowMultiple=k in self._multivalue_fields,
                        )
                    )

    @staticmethod
    def wrap_bytes(val: bytes) -> str:
        """
        Handles bytes values for uploading metadata
        The process is gzip -> base64

        :meta private:
        """
        compressed = gzip.compress(val)
        return base64.b64encode(compressed).decode("utf-8")

    def get_metadata_entries(self):
        return self._metadata_entries
