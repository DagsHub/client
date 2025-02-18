import base64
import datetime
import json
import logging
import tempfile
import os.path
import threading
import time
import uuid
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, Set, ContextManager, Tuple, Literal, Callable


import rich.progress
from dataclasses_json import config, LetterCase, DataClassJsonMixin
from pathvalidate import sanitize_filepath

import dagshub.common.config
from dagshub.common import rich_console
from dagshub.common.analytics import send_analytics_event
from dagshub.common.environment import is_mlflow_installed
from dagshub.common.helpers import prompt_user, http_request, log_message
from dagshub.common.rich_util import get_rich_progress
from dagshub.common.util import (
    lazy_load,
    multi_urljoin,
    to_timestamp,
    exclude_if_none,
    deprecated,
)
from dagshub.data_engine.annotation.importer import AnnotationImporter, AnnotationType, AnnotationLocation
from dagshub.data_engine.client.models import (
    PreprocessingStatus,
    MetadataFieldSchema,
    ScanOption,
    DatasetResult,
)
from dagshub.data_engine.dtypes import MetadataFieldType
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.errors import (
    WrongOperatorError,
    WrongOrderError,
    DatasetFieldComparisonError,
    FieldNotFoundError,
    DatasetNotFoundError,
)
from dagshub.data_engine.model.metadata import (
    validate_uploading_metadata,
    run_preupload_transforms,
    precalculate_metadata_info,
)
from dagshub.data_engine.model.metadata.transforms import DatasourceFieldInfo, _add_metadata
from dagshub.data_engine.model.metadata.dtypes import DatapointMetadataUpdateEntry
from dagshub.data_engine.model.metadata_field_builder import MetadataFieldBuilder
from dagshub.data_engine.model.query import QueryFilterTree
from dagshub.data_engine.model.schema_util import (
    default_metadata_type_value,
)
from dagshub.data_engine.model.datasource_state import DatasourceState

if TYPE_CHECKING:
    from dagshub.data_engine.model.query_result import QueryResult
    import fiftyone as fo
    import pandas
    import mlflow
    import mlflow.entities
    import cloudpickle
    import ngrok
else:
    plugin_server_module = lazy_load("dagshub.data_engine.voxel_plugin_server.server")
    fo = lazy_load("fiftyone")
    mlflow = lazy_load("mlflow")
    pandas = lazy_load("pandas")
    ngrok = lazy_load("ngrok")
    cloudpickle = lazy_load("cloudpickle")

logger = logging.getLogger(__name__)

LS_ORCHESTRATOR_URL = "http://127.0.0.1"
MLFLOW_DATASOURCE_TAG_NAME = "dagshub.datasets.datasource_id"
MLFLOW_DATASET_TAG_NAME = "dagshub.datasets.dataset_id"


@dataclass
class DatapointDeleteMetadataEntry(DataClassJsonMixin):
    datapointId: str
    key: str


@dataclass
class DatapointDeleteEntry(DataClassJsonMixin):
    datapointId: str


@dataclass
class Field:
    """
    Class used to define custom fields for use in \
    :func:`Datasource.select() <dagshub.data_engine.model.datasource.Datasource.select>` or in filtering.

    Example of filtering on old data from a field::

        t = datetime.now() - timedelta(days=2)
        q = ds[Field("size", as_of=t)] > 500
        q.all()
    """

    field_name: str
    """The database field where the values are stored. In other words, where to get the values from."""
    as_of: Optional[Union[float, datetime.datetime]] = None
    """
    If defined, the data in this field would be shown as of this moment in time.

    Accepts either a datetime object, or a UTC timestamp.
    """
    alias: Optional[str] = None
    """
    How the returned custom data field should be named.

    Useful when you're comparing the same field at multiple points in time::

        yesterday = datetime.now() - timedelta(days=1)

        ds.select(
            Field("value", alias="value_today"),
            Field("value", as_of=yesterday, alias="value_yesterday")
        ).all()
    """

    @property
    def as_of_timestamp(self) -> Optional[int]:
        if self.as_of is None:
            return None
        return to_timestamp(self.as_of)

    def to_dict(self, ds: "Datasource") -> Dict[str, Any]:
        if not ds.has_field(self.field_name):
            raise FieldNotFoundError(self.field_name)

        res_dict: Dict[str, Union[str, int, None]] = {"name": self.field_name}
        if self.as_of is not None:
            res_dict["asOf"] = self.as_of_timestamp
        if self.alias:
            res_dict["alias"] = self.alias
        return res_dict


_metadata_contexts: Dict[Union[int, str], "MetadataContextManager"] = {}


class Datasource:
    def __init__(
        self,
        datasource: "DatasourceState",
        query: Optional["DatasourceQuery"] = None,
        from_dataset: Optional["DatasetState"] = None,
    ):
        self._source = datasource
        if query is None:
            query = DatasourceQuery()
        self._query = query
        # this ref marks if source is currently used in
        # meta-data update 'with' block
        self._explicit_update_ctx: Optional[MetadataContextManager] = None
        self.assigned_dataset = from_dataset

        self.ngrok_listener = None

    @property
    def has_explicit_context(self):
        return self._explicit_update_ctx is not None

    @property
    def source(self) -> "DatasourceState":
        return self._source

    def clear_query(self, reset_to_dataset=True):
        """
        Clear the attached query.

        Args:
            reset_to_dataset: If ``True`` and this Datasource was saved as a dataset, reset to the query in the dataset,
                instead of clearing the query completely.
        """
        if reset_to_dataset and self.assigned_dataset is not None and self.assigned_dataset.query is not None:
            self._query = self.assigned_dataset.query.__deepcopy__()
        else:
            self._query = DatasourceQuery()

    def __deepcopy__(self, memodict={}) -> "Datasource":
        res = Datasource(self._source, self._query.__deepcopy__())
        res.assigned_dataset = self.assigned_dataset

        return res

    def get_query(self) -> "DatasourceQuery":
        return self._query

    @property
    def annotation_fields(self) -> List[str]:
        """Return all fields that have the annotation meta tag set"""
        return [f.name for f in self.fields if f.is_annotation()]

    @property
    def document_fields(self) -> List[str]:
        return [f.name for f in self.fields if f.is_document()]

    def serialize_gql_query_input(self) -> Dict:
        """
        Serialize the query of this Datasource for use in GraphQL querying (e.g. getting datapoints)

        :meta private:
        """
        return self._query.to_dict()

    def _deserialize_from_gql_result(self, query_dict: Dict):
        """
        Imports query information from ``query_dict``
        """
        self._query = DatasourceQuery.from_dict(query_dict)

    def load_from_dataset(
        self, dataset_id: Optional[Union[str, int]] = None, dataset_name: Optional[str] = None, change_query=True
    ):
        """
        Imports query information from a dataset with the specified id or name. Either of id or name could be specified

        Args:
            dataset_id: ID of the dataset
            dataset_name: Name of the dataset
            change_query: Whether to change the query of this object to the query in the dataset

        :meta private:
        """
        datasets = self.source.client.get_datasets(id=dataset_id, name=dataset_name)
        if not datasets:
            raise DatasetNotFoundError(self.source.repo, dataset_id, dataset_name)
        dataset_state = DatasetState.from_gql_dataset_result(datasets[0])
        self.load_from_dataset_state(dataset_state, change_query)

    def load_from_dataset_state(self, dataset_state: "DatasetState", change_query=True):
        """
        Imports query information from a :class:`~dagshub.data_engine.model.dataset_state.DatasetState`

        Args:
            dataset_state: State to load
            change_query: If false, only assigns the dataset.
                If true, also changes the query to be the query of the dataset

        :meta private:
        """
        if self.source.id != dataset_state.datasource_id:
            raise RuntimeError(
                "Dataset belongs to a different datasource "
                f"(This datasource: {self.source.id}, Dataset's datasource: {dataset_state.datasource_id})"
            )
        self.assigned_dataset = dataset_state
        if change_query:
            self._query = dataset_state.query

    def sample(self, start: Optional[int] = None, end: Optional[int] = None) -> "QueryResult":
        if start is not None:
            logger.warning("Starting slices is not implemented for now")
        res = self._source.client.sample(self, end, include_metadata=True)
        res._load_autoload_fields()
        return res

    def fetch(self, load_documents=True, load_annotations=True) -> "QueryResult":
        """
        Executes the query and returns a :class:`.QueryResult` object containing returned datapoints.

        If there's an active MLflow run, logs an artifact with information about the query to the run.

        This function respects the limit set on the query with :func:`limit()`.

        Args:
            load_documents: Automatically download all document blob fields
            load_annotations: Automatically download all annotation blob fields
        """
        self._check_preprocess()
        res = self._source.client.get_datapoints(self)
        self._autolog_mlflow(res)
        res._load_autoload_fields(documents=load_documents, annotations=load_annotations)

        return res

    def head(self, size=100, load_documents=True, load_annotations=True) -> "QueryResult":
        """
        Executes the query and returns a :class:`.QueryResult` object containing first ``size`` datapoints

        .. note::
            This function is intended for quick checks and debugging your queries.
            As a result of that, this function does not log an artifact to MLflow.
            If you want to limit the number of datapoints returned by the query as part of the training workflow,
            use :func:`limit()` instead. That will save the limit as part of the query.

        Args:
            size: how many datapoints to get. Default is 100
            load_documents: Automatically download all document blob fields
            load_annotations: Automatically download all annotation blob fields
        """
        self._check_preprocess()
        send_analytics_event("Client_DataEngine_DisplayTopResults", repo=self.source.repoApi)
        res = self._source.client.head(self, size)
        res._load_autoload_fields(documents=load_documents, annotations=load_annotations)
        return res

    def all(self, load_documents=True, load_annotations=True) -> "QueryResult":
        """
        Executes the query and returns a :class:`.QueryResult` object containing **all** datapoints

        If there's an active MLflow run, logs an artifact with information about the query to the run.

        .. warning::
            Unlike :func:`fetch()`, this function will override any limits set on the query.
            If you have set any limits on the query with :func:`limit()`, use :func:`fetch()` instead.

        Args:
            load_documents: Automatically download all document blob fields
            load_annotations: Automatically download all annotation blob fields
        """
        ds = self
        if self._query.limit:
            log_message(
                "Calling all() on a datasource with a limited query.\n"
                "This will override the limiting and get ALL datapoints in the current query.\n"
                "Use fetch() instead if you want to keep the datapoint limit.",
                logger,
            )
            ds = self.limit(None)
        return ds.fetch()

    def select(self, *selected: Union[str, Field]) -> "Datasource":
        """
        Select which fields should appear in the query result.

        If you want to query older versions of metadata,
        use :class:`Field` objects with ``as_of`` set to your desired time.

        By default, only the defined fields are returned.
        If you want to return all existing fields plus whatever additional fields you define,
        add ``"*"`` into the arguments.

        Args:
            selected: Fields you want to select. Can be either of:

                - Name of the field to select: ``"field"``.
                - ``"*"`` to select all the fields in the datasource.
                - :class:`Field` object.

        Example::

            t = datetime.now() - timedelta(hours=24)
            q1 = ds.select("*", Field("size", as_of=t, alias="size_asof_24h_ago"))
            q1.all()
        """

        include_all = False
        selects = []
        for s in selected:
            if isinstance(s, Field):
                selects.append(s.to_dict(self))
            else:
                if s != "*":
                    selects.append({"name": s})
                else:
                    include_all = True

        if include_all:
            aliases = set([s["alias"] for s in selects if "alias" in s])
            for f in self.fields:
                if f.name in aliases:
                    raise ValueError(
                        f"Alias {f.name} can't be used, because * was specified and "
                        f"a field with that name already exists"
                    )
                selects.append({"name": f.name})

        new_ds = self.__deepcopy__()
        new_ds.get_query().select = selects
        return new_ds

    def as_of(self, time: Union[float, datetime.datetime]) -> "Datasource":
        """
        Get a snapshot of the datasource's state as of ``time``.

        Args:
            time: At which point in time do you want to get data from.\
                Either a UTC timestamp or a ``datetime`` object.

        In the following example, you will get back datapoints that were created no later than yesterday AND \
        had their size at this point bigger than 5 bytes::

            t = datetime.now() - timedelta(hours=24)
            q1 = (ds["size"] > 5).as_of(t)
            q1.all()

        .. note::
            If used with :func:`select`, the ``as_of`` set on the fields takes precedence
            over the global query ``as_of`` set here.
        """
        new_ds = self.__deepcopy__()

        new_ds._query.as_of = to_timestamp(time)
        return new_ds

    def with_time_zone(self, tz_val: str) -> "Datasource":
        """
        A time zone offset string in the form of "+HH:mm" or "-HH:mm".

        A metadata of type datetime is always stored in DB as a UTC time, when a query is done on this field
        there are 3 options:

        - Metadata was saved with a timezone, in which case it will be used.

        - Metadata was saved without a timezone, in which case UTC will be used.

        - with_time_zone specified a time zone and it will override whatever is in the database.
        """
        new_ds = self.__deepcopy__()

        new_ds._query.time_zone = tz_val
        return new_ds

    def order_by(self, *args: Union[str, Tuple[str, Union[bool, str]]]) -> "Datasource":
        """
        Sort the query result by the specified fields.
        Any previously set order will be overwritten.

        Args:
            Fields to sort by. Can be either of:
                - Name of the field to sort by: ``"field"``.
                - A tuple of ``(field_name, ascending)``: ``("field", True)``.
                - A tuple of ``(field_name, "asc"|"desc")``: ``("field", "asc")``.

        Examples::

            ds.order_by("size").all()                   # Order by ascending size
            ds.order_by(("date", "desc"), "size).all()  # Order by descending date, then ascending size
        """
        new_ds = self.__deepcopy__()
        orders = []
        for arg in args:
            if isinstance(arg, str):
                orders.append({"field": arg, "order": "ASC"})
            else:
                if len(arg) != 2:
                    raise RuntimeError(
                        f"Invalid sort argument {arg}, must be a tuple (<field>, 'asc'|'desc'|True|False)"
                    )
                if isinstance(arg[1], bool):
                    order = "ASC" if arg[1] else "DESC"
                elif isinstance(arg[1], str) and arg[1].upper() in ["ASC", "DESC"]:
                    order = arg[1].upper()
                else:
                    raise RuntimeError(f"Invalid sort argument {arg}, second value must be 'asc'|'desc'|True|False")
                orders.append({"field": arg[0], "order": order})
        new_ds.get_query().order_by = orders
        return new_ds

    def limit(self, size: Optional[int]) -> "Datasource":
        """
        Limit the number of datapoints returned by the query.
        Use ``None`` to remove the limit.
        This argument is only respected when using :func:`fetch()`.

        Args:
            size: Number of datapoints to return. If ``None``, no limit is applied and all datapoints will be fetched.

        Example::

            ds.limit(10).fetch()
        """
        new_ds = self.__deepcopy__()
        new_ds._query.limit = size
        return new_ds

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
            New fields have to have their type defined using ``.set_type()`` before doing anything else

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

    @property
    def implicit_update_context(self) -> "MetadataContextManager":
        """
        Context that is used when updating metadata through ``dp[field] = value`` syntax, can be created on demand.

        :meta private:
        """
        key = self.source.id
        if key not in _metadata_contexts:
            _metadata_contexts[key] = MetadataContextManager(self)
        return _metadata_contexts[key]

    def upload_metadata_of_implicit_context(self):
        """
        commit meta data changes done in dictionary assignment context
        :meta private:
        """
        try:
            self._upload_metadata(self.implicit_update_context.get_metadata_entries())
        finally:
            self.implicit_update_context.clear()

    def metadata_context(self) -> ContextManager["MetadataContextManager"]:
        """
        Returns a metadata context, that you can upload metadata through using its
        :func:`~MetadataContextManager.update_metadata()` function.
        Once the context is exited, all metadata is uploaded in one batch::

            with ds.metadata_context() as ctx:
                ctx.update_metadata("file1", {"key1": True, "key2": "value"})

        """

        # Need to have the context manager inside a wrapper to satisfy MyPy + PyCharm type hinter
        @contextmanager
        def func():
            self.source.get_from_dagshub()
            send_analytics_event("Client_DataEngine_addEnrichments", repo=self.source.repoApi)
            ctx = MetadataContextManager(self)

            self._explicit_update_ctx = ctx
            yield ctx
            try:
                entries = ctx.get_metadata_entries() + self.implicit_update_context.get_metadata_entries()
                self._upload_metadata(entries)
            finally:
                # Clear the implicit context because it can persist
                self.implicit_update_context.clear()
                # The explicit one created with with: can go away
                self._explicit_update_ctx = None

        return func()

    def upload_metadata_from_file(
        self, file_path, path_column: Optional[Union[str, int]] = None, ingest_on_server: bool = False
    ):
        """
        Upload metadata from a file.

        Args:
            file_path: Path to the file with metadata. Allowed formats are CSV, Parquet, ZIP, GZ.
            path_column: Column with the datapoints' paths. Can either be the name of the column, or its index.
                If not specified, the first column is used.
            ingest_on_server: Set to ``True`` to process the metadata asynchronously.
                The file will be sent to our server and ingested into the datasource there.
                Default is ``False``.
        """
        send_analytics_event("Client_DataEngine_addEnrichmentsWithFile", repo=self.source.repoApi)

        if ingest_on_server:
            datasource_name = self.source.name
            self._source.import_metadata_from_file(datasource_name, file_path, path_column)
        else:
            df = self._convert_file_to_df(file_path)
            self.upload_metadata_from_dataframe(df, path_column, ingest_on_server)

    def upload_metadata_from_dataframe(
        self, df: "pandas.DataFrame", path_column: Optional[Union[str, int]] = None, ingest_on_server: bool = False
    ):
        """
        Upload metadata from a pandas dataframe.

        All columns are uploaded as metadata, and the path of every datapoint is taken from `path_column`.

        Args:
            df (`pandas.DataFrame <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_):
                DataFrame with metadata
            path_column: Column with the datapoints' paths. Can either be the name of the column, or its index.
                If not specified, the first column is used.
            ingest_on_server: Set to ``True`` to process the metadata asynchronously.
                The file will be sent to our server and ingested into the datasource there.
                Default is ``False``.
        """
        self.source.get_from_dagshub()
        send_analytics_event("Client_DataEngine_addEnrichmentsWithDataFrame", repo=self.source.repoApi)

        if ingest_on_server:
            self._remote_upload_metadata_from_dataframe(df, path_column)
        else:
            metadata = self._df_to_metadata(df, path_column, multivalue_fields=self._get_multivalue_fields())
            self._upload_metadata(metadata)

    def _remote_upload_metadata_from_dataframe(
        self, df: "pandas.DataFrame", path_column: Optional[Union[str, int]] = None
    ):
        datasource_name = self.source.name

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as tmp:
            file_path = tmp.name
            df.to_parquet(file_path, index=False)

            self._source.import_metadata_from_file(datasource_name, file_path, path_column)

    def _get_multivalue_fields(self) -> Set[str]:
        res = set()
        for col in self.source.metadata_fields:
            if col.multiple:
                res.add(col.name)
        return res

    def _generate_metadata_cache_info(self) -> DatasourceFieldInfo:
        return DatasourceFieldInfo(
            multivalue_fields=self._get_multivalue_fields(),
            field_value_types={f.name: f.valueType for f in self.fields},
            document_fields=self.document_fields,
        )

    def _df_to_metadata(
        self, df: "pandas.DataFrame", path_column: Optional[Union[str, int]] = None, multivalue_fields=set()
    ) -> List[DatapointMetadataUpdateEntry]:
        if path_column is None:
            path_column = df.columns[0]
        elif isinstance(path_column, str):
            if path_column not in df.columns:
                raise ValueError(f"Column {path_column} does not exist in the dataframe")
        elif isinstance(path_column, int):
            path_column = df.columns[path_column]

        # objects are actually mixed and not guaranteed to be string, but this should cover most use cases
        if df.dtypes[path_column] != "object":
            raise ValueError(f"Path column {path_column} must contain strings")

        field_info = self._generate_metadata_cache_info()
        res: List[DatapointMetadataUpdateEntry] = []

        for _, row in df.iterrows():
            datapoint = row[path_column]
            for key, val in row.items():
                if key == path_column:
                    continue
                key = str(key)
                _add_metadata(field_info, res, datapoint, key, val, is_pandas=True)
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

    def delete_dataset(self, force: bool = False):
        """
        Deletes the dataset, if this object was created from a dataset
        (e.g. from :func:`.datasets.get_dataset()`).

        This doesn't delete the underlying datasource and its metadata, only deleting the dataset and its query.

        If this datasource object wasn't created from a dataset, raises a ``ValueError``.

        Args:
            force: Skip the confirmation prompt
        """
        if self.assigned_dataset is None:
            raise ValueError("This datasource was not created from a dataset")
        prompt = (
            f'You are about to delete dataset "{self.assigned_dataset.dataset_name}" for repo "{self.source.repo}"\n'
            f'The datasource "{self.source.name}" will still exist, but the dataset entry will be removed'
        )
        if not force:
            user_response = prompt_user(prompt)
            if not user_response:
                print("Deletion cancelled")
                return
        self.source.client.delete_dataset(self.assigned_dataset.dataset_id)

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
        precalculated_info = precalculate_metadata_info(self, metadata_entries)
        validate_uploading_metadata(precalculated_info)
        run_preupload_transforms(self, metadata_entries, precalculated_info)

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

    def delete_metadata_from_datapoints(self, datapoints: List[Datapoint], fields: List[str]):
        """
        Delete metadata from datapoints.
        The deleted values can be accessed using versioned query with time set before the deletion

        Args:
            datapoints: datapoints to delete metadata from
            fields: fields to delete
        """
        metadata_entries = []
        for d in datapoints:
            for n in fields:
                metadata_entries.append(DatapointDeleteMetadataEntry(datapointId=d.datapoint_id, key=n))
        self.source.client.delete_metadata_for_datapoint(self, metadata_entries)

    def delete_datapoints(self, datapoints: List[Datapoint], force: bool = False):
        """
        Delete datapoints.

        - These datapoints will no longer show up in queries.
        - Does not delete the datapoint's file, only removing the data from the datasource.
        - You can still query these datapoints and associated metadata with \
        versioned queries whose time is before deletion time.
        - You can re-add these datapoints to the datasource by uploading new metadata to it with, for example, \
        :func:`Datasource.metadata_context <dagshub.data_engine.model.datasource.Datasource.metadata_context>`. \
        This will create a new datapoint with new id and new metadata records.
        - Datasource scanning will *not* add these datapoints back.

        Args:
            datapoints: list of datapoints objects to delete
            force: Skip the confirmation prompt
        """
        dps_str = "\n\t".join([""] + [d.path for d in datapoints])
        prompt = (
            f"You are about to delete the following datapoint(s): {dps_str}\n"
            f"This will remove the datapoint and metadata from unversioned queries, "
            f"but won't delete the underlying file."
        )
        if not force:
            user_response = prompt_user(prompt)
            if not user_response:
                print("Deletion cancelled")
                return

        self.source.client.delete_datapoints(
            self, [DatapointDeleteEntry(datapointId=d.datapoint_id) for d in datapoints]
        )

    def save_dataset(self, name: str) -> "Datasource":
        """
        Save the dataset, which is a combination of datasource + query, on the backend.
        That way you can persist and share your queries.
        You can get the dataset back later by calling :func:`.datasets.get_dataset()`

        Args:
            name: Name of the dataset

        Returns:
            A datasource object with the dataset assigned to it
        """
        send_analytics_event("Client_DataEngine_QuerySaved", repo=self.source.repoApi)

        self.source.client.save_dataset(self, name)
        log_message(f"Dataset {name} saved")

        copy_with_ds_assigned = self.__deepcopy__()
        copy_with_ds_assigned.load_from_dataset(dataset_name=name, change_query=False)
        return copy_with_ds_assigned

    @deprecated("Either use autologging, or QueryResult.log_to_mlflow() if autologging is turned off")
    def log_to_mlflow(
        self,
        artifact_name: Optional[str] = None,
        run: Optional["mlflow.entities.Run"] = None,
        as_of: Optional[datetime.datetime] = None,
    ) -> "mlflow.entities.Run":
        """
        Logs the current datasource state to MLflow as an artifact.

        .. warning::
            This function is deprecated. Use autologging or
            :func:`QueryResult.log_to_mlflow() <dagshub.data_engine.model.query_result.QueryResult.log_to_mlflow>`
            instead.

        Args:
            artifact_name: Name of the artifact that will be stored in the MLflow run.
            run: MLflow run to save to. If ``None``, uses the active MLflow run or creates a new run.
            as_of: The querying time for which to save the artifact.
                Any time the datasource is recreated from the artifact, it will be queried as of this timestamp.
                If None, the current machine time will be used.
                If the artifact is autologged to MLflow (will happen if you have an active MLflow run),
                then the timestamp of the query will be used.

        Returns:
            Run to which the artifact was logged.
        """
        if artifact_name is None:
            as_of = as_of or (self._query.as_of or datetime.datetime.now())
            artifact_name = self._get_mlflow_artifact_name("log", as_of)
        elif not artifact_name.endswith(".dagshub.dataset.json"):
            artifact_name += ".dagshub.dataset.json"

        return self._log_to_mlflow(artifact_name, run, as_of)

    def _autolog_mlflow(self, qr: "QueryResult"):
        if not is_mlflow_installed:
            return
        # Run ONLY if there's an active run going on
        active_run = mlflow.active_run()
        if active_run is None:
            return

        artifact_name = self._get_mlflow_artifact_name("autolog", qr.query_data_time)

        threading.Thread(
            target=self._log_to_mlflow,
            kwargs={"artifact_name": artifact_name, "run": active_run, "as_of": qr.query_data_time},
        ).start()

    def _log_to_mlflow(
        self,
        artifact_name,
        run: Optional["mlflow.entities.Run"] = None,
        as_of: Optional[datetime.datetime] = None,
    ) -> "mlflow.Entities.Run":
        if run is None:
            run = mlflow.active_run()
            if run is None:
                run = mlflow.start_run()
        client = mlflow.MlflowClient()
        client.set_tag(run.info.run_id, MLFLOW_DATASOURCE_TAG_NAME, self.source.id)
        if self.assigned_dataset is not None:
            client.set_tag(run.info.run_id, MLFLOW_DATASET_TAG_NAME, self.assigned_dataset.dataset_id)
        client.log_dict(run.info.run_id, self._to_dict(as_of), artifact_name)
        log_message(f'Saved the datasource state to MLflow (run "{run.info.run_name}") as "{artifact_name}"')
        return run

    def _get_mlflow_artifact_name(self, prefix: str, as_of: datetime.datetime) -> str:
        now_time = as_of.strftime("%Y-%m-%dT%H-%M-%S")  # Not ISO format to make it a valid filename
        uuid_chunk = str(uuid.uuid4())[-4:]
        return f"{prefix}_{self.source.name}_{now_time}_{uuid_chunk}.dagshub.dataset.json"

    def save_to_file(self, path: Union[str, PathLike] = ".") -> Path:
        """
        Saves a JSON file representing the current state of datasource or dataset.
        Useful for connecting code versions to the datasource used for training.

        .. note::
            Does not save the actual contents of the datasource/dataset, only the query.

        Args:
            path: Where to save the file. If path is an existing folder, saves to ``<path>/<ds_name>.json``.

        Returns:
            The path to the saved file
        """
        path = Path(path)
        if path.is_dir():
            if self.assigned_dataset is not None:
                name = self.assigned_dataset.dataset_name
            else:
                name = self.source.name
            path = path / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        res = self._to_dict()
        with open(path, "w") as file:
            json.dump(res, file, indent=4, sort_keys=True)
        log_message(f"Datasource saved to '{path}'")

        return path

    def _serialize(self, as_of: datetime.datetime) -> "DatasourceSerializedState":
        res = DatasourceSerializedState(
            repo=self.source.repo,
            datasource_id=self.source.id,
            datasource_name=self.source.name,
            query=self._query,
            timestamp=as_of.timestamp(),
            modified=self.is_query_different_from_dataset,
            link=self._generate_visualize_url(),
        )
        if self.assigned_dataset is not None:
            res.dataset_id = self.assigned_dataset.dataset_id
            res.dataset_name = self.assigned_dataset.dataset_name
        if self._query.as_of is not None:
            res.timed_link = res.link
        elif as_of is not None:
            timed_ds = self.as_of(as_of)
            res.timed_link = timed_ds._generate_visualize_url()
        return res

    def _to_dict(self, as_of: Optional[datetime.datetime] = None) -> Dict:
        if as_of is None:
            as_of = datetime.datetime.now()
        res = self._serialize(as_of).to_dict()
        # Skip Nones in the result
        res = {k: v for k, v in res.items() if v is not None}
        return res

    @property
    def is_query_different_from_dataset(self) -> Optional[bool]:
        """
        Is the current query of the object different from the one in the assigned dataset.

        If no dataset is assigned, returns ``None``.
        """
        if self.assigned_dataset is None:
            return None
        return self._query.to_dict() != self.assigned_dataset.query.to_dict()

    @staticmethod
    def load_from_serialized_state(state_dict: Dict) -> "Datasource":
        """
        Load a Datasource that was saved with :func:`save_to_file`

        Args:
            state_dict: Serialized JSON object
        """

        state = DatasourceSerializedState.from_dict(state_dict)
        # The json_dataclasses.from_dict() doesn't respect the default value hints, so we fill it out for it
        state.query._fill_out_defaults()

        ds_state = DatasourceState(repo=state.repo, name=state.datasource_name, id=state.datasource_id)
        ds_state.get_from_dagshub()
        ds = Datasource(ds_state)
        ds._query = state.query

        if state.dataset_id is not None:
            ds.load_from_dataset(state.dataset_id, state.dataset_name, change_query=False)

        if state.timestamp is not None:
            ds = ds.as_of(datetime.datetime.fromtimestamp(state.timestamp, tz=datetime.timezone.utc))

        return ds

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

    def visualize(self, visualizer: Literal["dagshub", "fiftyone"] = "dagshub", **kwargs) -> Union[str, "fo.Session"]:
        """
        Visualize the whole datasource using
        :func:`QueryResult.visualize() <dagshub.data_engine.model.query_result.QueryResult.visualize>`.

        Read the function docs for kwarg documentation.
        """
        if visualizer == "dagshub":
            link = self._generate_visualize_url()

            print("The visualization is available at the following link:")
            print(link)

            webbrowser.open(link)

            return link

        elif visualizer == "fiftyone":
            return self.all().visualize(**kwargs)

    def _generate_visualize_url(self) -> str:
        url: str
        if self.assigned_dataset is not None:
            url = multi_urljoin(
                self.source.repoApi.repo_url, f"datasets/dataset/{self.assigned_dataset.dataset_id}/gallery"
            )
        else:
            url = self.source.url

        full_url = url
        query = self._encode_query_for_frontend()
        if query is not None:
            full_url += f"?{query}"
        return full_url

    def _encode_query_for_frontend(self) -> str:
        """
        Returns a query that is parseable by the frontend.
        It has to be a JSON of the GraphQL query, encoded into b64

        This also omits any null values to make the resulting URL shorter
        """
        params_dict = self._query.to_dict()
        params_dict = {k: v for k, v in params_dict.items() if v is not None}
        params = json.dumps(params_dict)
        params_encoded = base64.urlsafe_b64encode(params.encode("utf-8")).decode("utf-8")
        return f"query={params_encoded}"

    @property
    def fields(self) -> List[MetadataFieldSchema]:
        return self.source.metadata_fields

    async def add_annotation_model_from_config(self, config, project_name, ngrok_authtoken, port=9090):
        """
        Initialize a LS backend for ML annotation using a preset configuration.

        Args:
            config: dictionary containing information about the mlflow model, hooks and LS label config
            recommended to use with `get_config()` from preconfigured_models in the orchestrator repo
            project_name: automatically adds backend to project
            ngrok_authtoken: uses ngrok to forward local connection
            port: (optional, default: 9090) port on which orchestrator is hosted
        """
        projects = self.source.repoApi.list_annotation_projects()

        if project_name not in projects:
            self.source.repoApi.add_annotation_project(project_name, config.pop("label_config"))
        else:
            self.source.repoApi.update_label_studio_project_config(project_name, config.pop("label_config"))

        await self.add_annotation_model(**config, port=port, project_name=project_name, ngrok_authtoken=ngrok_authtoken)

    async def add_annotation_model(
        self,
        repo: str,
        name: str,
        version: str = "latest",
        post_hook: Callable[[Any], Any] = lambda x: x,
        pre_hook: Callable[[Any], Any] = lambda x: x,
        port: int = 9090,
        project_name: Optional[str] = None,
        ngrok_authtoken: Optional[str] = None,
    ) -> None:
        """
        Initialize a LS backend for ML annotation.

        Args:
            repo: repository to extract the model from
            name: name of the model in the mlflow registry
            version: (optional, default: 'latest') version of the model in the mlflow registry
            pre_hook: (optional, default: identity function) function that runs before datapoint is sent to the model
            post_hook: (optional, default: identity function) function that converts mlflow model output
            to the desired format
            port: (optional, default: 9090) port on which orchestrator is hosted
            project_name: (optional, default: None) automatically adds backend to project
            ngrok_authtoken: (optional, default: None) uses ngrok to forward local connection
        """

        def fn_encoder(fn):
            return base64.b64encode(cloudpickle.dumps(fn)).decode("utf-8")

        if not ngrok_authtoken and project_name:
            raise ValueError("As `ngrok_authtoken` is not specified, project will have to be added manually.")
        with get_rich_progress() as progress:
            task = progress.add_task("Initializing LS Model...", total=1)
            res = http_request(
                "POST",
                f"{LS_ORCHESTRATOR_URL}:{port}/configure",
                headers={"Content-Type": "application/json"},
                json=json.dumps(
                    {
                        "host": self.source.repoApi.host,
                        "username": self.source.repoApi.owner,
                        "repo": repo,
                        "model": name,
                        "version": version,
                        "authtoken": dagshub.auth.get_token(),
                        "datasource_repo": self.source.repo,
                        "datasource_name": self.source.name,
                        "pre_hook": fn_encoder(pre_hook),
                        "post_hook": fn_encoder(post_hook),
                    }
                ),
            )
            progress.update(task, advance=1, description="Configured LS model backend container")
            if res.status_code // 100 != 2:
                raise ValueError(f"Adding backend failed! Response: {res.text}")

            if ngrok_authtoken:
                if not self.ngrok_listener:
                    self.ngrok_listener = await ngrok.forward(port, authtoken=ngrok_authtoken)
                endpoint = self.ngrok_listener.url()
            else:
                endpoint = f"{LS_ORCHESTRATOR_URL}:{port}/"
            progress.update(task, advance=1, description="Configured any necessary forwarding")

            if project_name:
                self.source.repoApi.add_autolabelling_endpoint(project_name, endpoint)
            else:
                progress.update(task, advance=1, description="Added model to LS backend")
                print(f"Connection Established! Add LS endpoint: {endpoint} to your project.")

    def annotate(self, fields_to_embed=None, fields_to_exclude=None) -> Optional[str]:
        """
        Sends all datapoints in the datasource for annotation in Label Studio.

        Args:
            fields_to_embed: list of meta-data columns that will show up in Label Studio UI.
             if not specified all will be displayed.
            fields_to_exclude: list of meta-data columns that will not show up in Label Studio UI

        .. note::
            This will send ALL datapoints in the datasource for annotation.
            It's recommended to not send a huge amount of datapoints to be annotated at once, to avoid overloading
            the Label Studio workspace.
            Use :func:`QueryResult.annotate() <dagshub.data_engine.model.query_result.QueryResult.annotate>`
            to annotate a result of a query with less datapoints.
            Alternatively, use a lower level :func:`send_datapoints_to_annotation` function

        :return: Link to open Label Studio in the browser
        """
        return self.all().annotate(fields_to_exclude=fields_to_exclude, fields_to_embed=fields_to_embed)

    def send_to_annotation(self):
        """
        deprecated, see :func:`annotate()`

        :meta private:
        """
        return self.annotate()

    def send_datapoints_to_annotation(
        self,
        datapoints: Union[List[Datapoint], "QueryResult", List[Dict]],
        open_project=True,
        ignore_warning=False,
        fields_to_exclude=None,
        fields_to_embed=None,
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
            fields_to_embed: list of meta-data columns that will show up in Label Studio UI.
             if not specified all will be displayed.
            fields_to_exclude: list of meta-data columns that will not show up in Label Studio UI
        Returns:
            Link to open Label Studio in the browser
        """
        for f in (fields_to_embed or []) + (fields_to_exclude or []):
            if not self.has_field(f):
                raise FieldNotFoundError(f)

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

        req_data = {
            "datasource_id": self.source.id,
            "datapoints": [],
            "ls_meta_excludes": fields_to_exclude,
            "ls_meta_includes": fields_to_embed,
        }

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

        def _check():
            reserved_searchable_fields = ["path"]
            fields = (f.name for f in self.fields)
            return field_name in reserved_searchable_fields or field_name in fields

        res = _check()
        # Refetch fields once - maybe things got updated
        if not res:
            self.source.get_from_dagshub()
            res = _check()

        return res

    def __repr__(self):
        res = f"Datasource {self.source.name}"
        res += f"\n\tRepo: {self.source.repo}, path: {self.source.path}"
        if self.assigned_dataset:
            res += (
                f"\n\tAssigned Dataset: {self.assigned_dataset.dataset_name} "
                f"(Query was modified: {self.is_query_different_from_dataset})"
            )
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

    def __getitem__(self, other: Union[slice, str, "Datasource", "Field"]):
        # Slicing - get items from the slice
        if type(other) is slice:
            return self.sample(other.start, other.stop)

        # Otherwise we're doing querying
        new_ds = self.__deepcopy__()
        if isinstance(other, (str, Field)):
            query_field: Field = Field(other) if isinstance(other, str) else other
            other_query = QueryFilterTree(
                query_field.field_name,
                query_field.as_of_timestamp,
            )
            if not self.has_field(query_field.field_name):
                raise FieldNotFoundError(query_field.field_name)
            if self._query.filter.is_empty:
                new_ds._query.filter = other_query
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
        if not isinstance(other, (int, float, str, datetime.datetime)):
            raise NotImplementedError
        return self.add_query_op("gt", other)

    def __ge__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str, datetime.datetime)):
            raise NotImplementedError
        return self.add_query_op("ge", other)

    def __le__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str, datetime.datetime)):
            raise NotImplementedError
        return self.add_query_op("le", other)

    def __lt__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if not isinstance(other, (int, float, str, datetime.datetime)):
            raise NotImplementedError
        return self.add_query_op("lt", other)

    def __eq__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if other is None:
            return self.is_null()
        if not isinstance(other, (int, float, str, datetime.datetime)):
            raise NotImplementedError
        return self.add_query_op("eq", other)

    def __ne__(self, other: object):
        self._test_not_comparing_other_ds(other)
        if other is None:
            return self.is_not_null()
        if not isinstance(other, (int, float, str, datetime.datetime)):
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

    def _periodic_filter(self, periodtype, items):
        periods = [str(s) for s in items]
        return self.add_query_op(periodtype, periods)

    def date_field_in_years(self, *item: int):
        """
        Checks if a metadata field (which is of datetime type) is in one of given years list.

        Args:
            List of years.

        Examples::

            datasource[(datasource["y"].date_field_in_years(1979, 2003)

        """

        return self._periodic_filter("year", item)

    def date_field_in_months(self, *item: int):
        """
        Checks if a metadata field (which is of datetime type) is in one of given months list.

        Args:
            List of months.

        Examples::

            datasource[(datasource["y"].date_field_in_months(12, 2)

        """
        return self._periodic_filter("month", item)

    def date_field_in_days(self, *item: int):
        """
        Checks if a metadata field (which is of datetime type) is in one of given days list.

        Args:
            List of days.

        Examples::

            datasource[(datasource["y"].date_field_in_days(25, 2)

        """
        return self._periodic_filter("day", item)

    def date_field_in_timeofday(self, item: str):
        """
        Checks if a metadata field (which is of datetime type) is in given minute range inside the day (any day).
        range is in the format of: "HH:mm-HH:mm" (or "HH:mm:ss-HH:mm:ss") where start hour is on the left.
        a range that starts at one day and ends at next day,
        should be expressed as OR of 2 range filter.

        Args:
            Time range string.

        Examples::

            datasource[(datasource["y"].date_field_in_timeofday("11:30-12:30")

        """
        self._test_not_comparing_other_ds(item)
        return self.add_query_op("timeofday", item)

    def startswith(self, item: str):
        """
        Check if the filtering field starts with the specified string item.

        :meta private:
        """
        if type(item) is not str:
            return WrongOperatorError(f"Cannot use startswith with non-string value {item}")
        return self.add_query_op("startswith", item)

    def endswith(self, item: str):
        """
        Check if the filtering field ends with the specified string item.

        :meta private:
        """
        if type(item) is not str:
            return WrongOperatorError(f"Cannot use endswith with non-string value {item}")
        return self.add_query_op("endswith", item)

    def is_null(self):
        """
        Check if the filtering field is null.

        :meta private:
        """
        field = self._get_filtering_field()
        val = default_metadata_type_value(field.valueType)
        return self.add_query_op("isnull", val)

    def is_not_null(self):
        """
        Check if the filtering field is not null.

        :meta private:
        """
        field = self._get_filtering_field()
        val = default_metadata_type_value(field.valueType)
        return self.add_query_op("!isnull", val)

    def _get_filtering_field(self) -> MetadataFieldSchema:
        field_name = self.get_query().filter.column_filter
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
        self,
        op: str,
        other: Optional[Union[str, int, float, "Datasource", "QueryFilterTree", List[str], datetime.datetime]] = None,
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

    @staticmethod
    def _convert_file_to_df(file_path: str):
        # prepare dataframe for import_metadata
        if file_path.lower().endswith(".csv"):
            df = pandas.read_csv(file_path)
        elif file_path.lower().endswith(".parquet"):
            df = pandas.read_parquet(file_path)
        elif file_path.lower().endswith(".zip"):
            df = pandas.read_csv(file_path, compression="zip")
        elif file_path.lower().endswith(".gz"):
            df = pandas.read_csv(file_path, compression="gzip")
        else:
            raise RuntimeError(
                f"File '{file_path}' needs to be a .csv/.parquet or a compressed .zip/.gz to be imported"
            )
        return df

    def import_annotations_from_files(
        self,
        annotation_type: AnnotationType,
        path: Union[str, Path],
        field: str = "imported_annotation",
        load_from: Optional[AnnotationLocation] = None,
        remapping_function: Optional[Callable[[str], str]] = None,
        **kwargs,
    ):
        """
        Imports annotations into the datasource from files

        The annotations will be downloaded and converted into Label Studio tasks,
        that are then uploaded into the specified fields.

        If the annotations are stored in a repo and not locally, they are downloaded to a temporary directory.

        Caveats:
            - YOLO:
                - Images need to also be downloaded to get their dimensions.
                - The .YAML file needs to have the ``path`` argument set to the relative path to the data. \
                    We're using that to download the files
                - You have to specify the ``yolo_type`` kwarg with the type of annotation to import

        Args:
            annotation_type: Type of annotations to import. Possible values are ``yolo`` and ``cvat``
            path: If YOLO - path to the .yaml file, if CVAT - path to the .zip file. \
                Can be either on disk or in repository
            field: Which field to upload the annotations into. \
                If it's an existing field, it has to be a blob field, \
                and it will have the annotations flag set afterwards.
            load_from: Force specify where to get the files from. \
                By default, we're trying to load files from the disk first, and then repository.
                If this is specified, then that check is being skipped and \
                we'll try to download from the specified location.
            remapping_function: Function that maps from a path of the annotation to the path of the datapoint. \
                If None, we try to make a best guess based on the first imported annotation. \
                This might fail, if there is no matching datapoint in the datasource for some annotations \
                or if the paths are wildly different.

        Keyword Args:
            yolo_type: Type of YOLO annotations to import. Either ``bbox``, ``segmentation`` or ``pose``.

        Example to import segmentation annotations into an ``imported_annotations`` field,
        using YOLO information from an ``annotations.yaml`` file (can be local, or in the repo)::

            ds.import_annotations_from_files(
                annotation_type="yolo",
                path="annotations.yaml",
                field="imported_annotations",
                yolo_type="segmentation"
            )
        """

        # Make sure the annotation field exists, is a blob field + has the annotation tag
        existing_fields = [f for f in self.fields if f.name == field]
        if len(existing_fields) != 0:
            f = existing_fields[0]
            if f.valueType != MetadataFieldType.BLOB:
                raise RuntimeError(
                    f"Field {f.name} is not a blob field. "
                    f"Choose a new field or an existing blob field to upload annotations to."
                )
        self.metadata_field(field).set_type(bytes).set_annotation().apply()

        # Run import
        importer = AnnotationImporter(
            ds=self,
            annotations_type=annotation_type,
            annotations_file=path,
            load_from=load_from,
            **kwargs,
        )
        annotation_dict = importer.import_annotations()

        annotation_dict = importer.remap_annotations(annotation_dict, remap_func=remapping_function)

        with rich_console.status("Converting annotations to tasks..."):
            tasks = importer.convert_to_ls_tasks(annotation_dict)

        with self.metadata_context() as ctx:
            for dp, task in tasks.items():
                ctx.update_metadata(dp, {field: task})

        log_message(f'Done! Uploaded annotations for {len(tasks)} datapoints to field "{field}"')


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

        field_info = self._datasource._generate_metadata_cache_info()

        for dp in datapoints:
            for k, v in metadata.items():
                _add_metadata(field_info, self._metadata_entries, dp, k, v, is_pandas=False)

    def get_metadata_entries(self):
        return self._metadata_entries

    def clear(self):
        self._metadata_entries.clear()

    def __len__(self):
        return len(self._metadata_entries)


@dataclass
class DatasourceQuery(DataClassJsonMixin):
    as_of: Optional[int] = field(default=None, metadata=config(exclude=exclude_if_none, letter_case=LetterCase.CAMEL))
    time_zone: Optional[str] = field(
        default=None, metadata=config(exclude=exclude_if_none, letter_case=LetterCase.CAMEL)
    )
    select: Optional[List[Dict]] = field(default=None, metadata=config(exclude=exclude_if_none))
    filter: "QueryFilterTree" = field(
        default_factory=QueryFilterTree,
        metadata=config(field_name="query", encoder=QueryFilterTree.serialize, decoder=QueryFilterTree.deserialize),
    )
    order_by: Optional[List] = field(
        default=None, metadata=config(exclude=exclude_if_none, letter_case=LetterCase.CAMEL)
    )
    limit: Optional[int] = field(default=None, metadata=config(exclude=exclude_if_none))

    def _fill_out_defaults(self):
        """For functions that don't utilize the default hints of the dataclass"""
        self.filter = QueryFilterTree()

    def __deepcopy__(self, memodict={}):
        other = DatasourceQuery(
            as_of=self.as_of,
            time_zone=self.time_zone,
            filter=self.filter.__deepcopy__(),
            limit=self.limit,
        )
        if self.select is not None:
            other.select = self.select.copy()
        if self.order_by is not None:
            other.order_by = self.order_by.copy()
        return other

    def compose(
        self, op: str, other: Optional[Union[str, int, float, "DatasourceQuery", "QueryFilterTree", "Datasource"]]
    ):
        other_query: Optional["DatasourceQuery"] = None
        # Extract the filter tree for composition
        if isinstance(other, (DatasourceQuery, Datasource)):
            if type(other) is Datasource:
                other = other.get_query()
            other_query = other
            other = other.filter

        self.filter.compose(op, other)

        # If composition went successfully, carry over the as_of, select and order_by from the other query
        if other_query is not None:
            if other_query.select is not None:
                self.select = other_query.select
            if other_query.as_of is not None:
                self.as_of = other_query.as_of
            if other_query.time_zone is not None:
                self.time_zone = other_query.time_zone
            if other_query.order_by is not None:
                self.order_by = other_query.order_by


@dataclass
class DatasourceSerializedState(DataClassJsonMixin):
    """
    Serialized state of the datasource.
    This should be enough to recreate the exact copy of the datasource back (with additional requests)

    Also carries additional information that might be useful for the user:
        - if the state of the datasource at the point of saving differed from the dataset
        - the timestamp of saving
        - link to open the datasource on DagsHub
    """

    repo: str
    """Repository this datasource is on"""
    datasource_id: Union[str, int]
    """ID of the datasource"""
    datasource_name: str
    """Name of the datasource"""
    query: DatasourceQuery
    """Query at the time of saving"""
    dataset_id: Optional[Union[str, int]] = None
    """ID of the assigned dataset"""
    dataset_name: Optional[str] = None
    """Name of the assigned dataset"""
    timestamp: Optional[float] = None
    """Timestamp of serialization"""
    modified: Optional[bool] = None
    """Does the query differ from the query in the assigned dataset"""
    link: Optional[str] = None
    """URL to open this datasource on DagsHub"""
    timed_link: Optional[str] = None
    """URL to open this datasource with the data at the time of querying"""


@dataclass
class DatasetState:
    """
    Information about the Dataset.

    Dataset is a Datasource with a Query applied on it.
    """

    dataset_id: Union[str, int]
    """
    ID of the dataset
    """
    dataset_name: str
    """
    Name of the dataset
    """
    datasource_id: Union[str, int]
    """
    ID of the datasource with which this dataset is associated
    """
    query: DatasourceQuery
    """
    Query of this dataset
    """

    @staticmethod
    def from_dataset_query(
        dataset_id: Union[str, int], dataset_name: str, datasource_id: Union[str, int], dataset_query: Union[Dict, str]
    ) -> "DatasetState":
        if type(dataset_query) is str:
            dataset_query = json.loads(dataset_query)
        query = DatasourceQuery.from_dict(dataset_query)
        res = DatasetState(dataset_id=dataset_id, dataset_name=dataset_name, datasource_id=datasource_id, query=query)
        return res

    @staticmethod
    def from_gql_dataset_result(dataset_result: "DatasetResult") -> "DatasetState":
        return DatasetState.from_dataset_query(
            dataset_id=dataset_result.id,
            dataset_name=dataset_result.name,
            datasource_id=dataset_result.datasource.id,
            dataset_query=dataset_result.datasetQuery,
        )
