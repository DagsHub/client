import datetime
import logging
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Callable, TYPE_CHECKING, Literal, Sequence

from tenacity import Retrying, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception_type

from dagshub.common.download import download_files
from dagshub.common.helpers import http_request
from dagshub.data_engine.annotation import MetadataAnnotations
from dagshub.data_engine.client.models import MetadataSelectFieldSchema, DatapointHistoryResult
from dagshub.data_engine.dtypes import MetadataFieldType

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

_generated_fields: Dict[str, Callable[["Datapoint"], Any]] = {
    "path": lambda dp: dp.path,
    "datapoint_id": lambda dp: dp.datapoint_id,
    "dagshub_download_url": lambda dp: dp.download_url,
}

logger = logging.getLogger(__name__)


@dataclass
class Datapoint:
    datapoint_id: int
    """
    ID of the datapoint in the database
    """
    path: str
    """
    Path of the datapoint, relative to the root of the datasource
    """
    metadata: Dict[str, Any]
    """
    Dictionary with the metadata
    """
    datasource: "Datasource"
    """
    Datasource this datapoint is from
    """

    def __getitem__(self, item):
        gen_field = _generated_fields.get(item)
        if gen_field is not None:
            return gen_field(self)
        return self.metadata[item]

    def __setitem__(self, key, value):
        if isinstance(value, MetadataAnnotations):
            value = value.to_ls_task()
        self.datasource.implicit_update_context.update_metadata(self.path, {key: value})

    def delete_metadata(self, *fields: str):
        """
        Delete metadata from this datapoint.

        The deleted values can be accessed using versioned query with time set before the deletion.

        Args:
            fields: fields to delete
        """
        self.datasource.delete_metadata_from_datapoints([self], list(fields))

    def delete(self, force: bool = False):
        """
        Delete this datapoint.

        - This datapoint will no longer show up in queries.
        - Does not delete the datapoint's file, only removing the data from the datasource.
        - You can still query this datapoint and associated metadata with \
            versioned queries whose time is before deletion time.
        - You can re-add this datapoint to the datasource by uploading new metadata to it with, for example, \
            :func:`Datasource.metadata_context <dagshub.data_engine.model.datasource.Datasource.metadata_context>`. \
            This will create a new datapoint with new id and new metadata records.
        - Datasource scanning will *not* add this datapoint back.

        Args:
            force: Skip the confirmation prompt
        """
        self.datasource.delete_datapoints([self], force=force)

    def save(self):
        """
        Commit changes to metadata done with one or more dictionary assignment syntax usages.
        `Learn more here <https://dagshub.com/docs/use_cases/data_engine/enrich_datasource\
        /#3-enriching-with-with-dictionary-like-assignment>`_.

        Example::

            specific_data_point['metadata_field_name'] = 42
            specific_data_point.save()

        """

        # if in context block, don't _upload_metadata, it will be done at context end
        if not self.datasource.has_explicit_context:
            self.datasource.upload_metadata_of_implicit_context()

    @property
    def download_url(self):
        """
        str: URL that can be used to download the datapoint's file from DagsHub
        """
        return self.datasource.source.raw_path(self)

    @property
    def path_in_repo(self):
        """
        Path of the datapoint in repo

        :rtype: `PurePosixPath <https://docs.python.org/3/library/pathlib.html#pathlib.PurePosixPath>`_
        """
        return self.datasource.source.file_path(self)

    @staticmethod
    def from_gql_edge(edge: Dict, datasource: "Datasource", fields: List[MetadataSelectFieldSchema]) -> "Datapoint":
        res = Datapoint(
            datapoint_id=int(edge["node"]["id"]),
            path=edge["node"]["path"],
            metadata={},
            datasource=datasource,
        )

        float_fields = {f.name for f in fields if f.valueType == MetadataFieldType.FLOAT}
        date_fields = {f.name for f in fields if f.valueType == MetadataFieldType.DATETIME}

        for meta_dict in edge["node"]["metadata"]:
            key = meta_dict["key"]
            value = meta_dict["value"]
            if key in float_fields:
                value = float(value)
            else:
                if key in date_fields:
                    timezone = meta_dict.get("timeZone")
                    value = _datetime_from_timestamp(value / 1000, timezone or "+00:00")
            res.metadata[key] = value
        return res

    def to_dict(self, metadata_keys: Sequence[str]) -> Dict[str, Any]:
        # Set the autogenerated fields
        res_dict = {k: v(self) for k, v in _generated_fields.items()}
        res_dict.update({key: self.metadata.get(key) for key in metadata_keys})
        return res_dict

    def get_blob(self, column: str, cache_on_disk=True, store_value=False) -> bytes:
        """
        Returns the blob stored in a binary column

        Args:
            column: where to get the blob from
            cache_on_disk: whether to store the downloaded blob on disk.
                If you store the blob on disk, then it won't need to be re-downloaded in the future.
                The contents of datapoint[column] will change to be the path of the blob on the disk.
            store_value: whether to store the blob in memory on the field attached to this datapoint,
                which will make its value accessible later using datapoint[column]
        """
        current_value = self.metadata[column]

        if type(current_value) is bytes:
            # Bytes - it's already there!
            return current_value
        if isinstance(current_value, Path):
            # Path - assume the path exists and is already downloaded,
            #   because it's unlikely that the user has set it themselves
            with current_value.open("rb") as f:
                content = f.read()
            if store_value:
                self.metadata[column] = content
            return content

        elif type(current_value) is str:
            # String - This is probably the hash of the blob, get that from dagshub
            blob_url = self.blob_url(current_value)
            blob_location = self.blob_cache_location / current_value

            # Make sure that the cache location exists
            if cache_on_disk:
                self.blob_cache_location.mkdir(parents=True, exist_ok=True)

            content = _get_blob(blob_url, blob_location, self.datasource.source.repoApi.auth, cache_on_disk, True)
            if type(content) is str:
                raise RuntimeError(f"Error while downloading blob: {content}")

            if store_value:
                self.metadata[column] = content
            elif cache_on_disk:
                self.metadata[column] = blob_location

            return content
        else:
            raise ValueError(f"Can't extract blob metadata from value {current_value} of type {type(current_value)}")

    def download_file(
        self, target: Optional[Union[PathLike, str]] = None, keep_source_prefix=True, redownload=False
    ) -> PathLike:
        """
        Downloads the datapoint to the target_dir directory

        Args:
            target: Where to download the file (either a directory, or the full path).\
                If not specified, then downloads to\
                :func:`datasource's default location \
                <dagshub.data_engine.model.datasource.Datasource.default_dataset_location>`.
            keep_source_prefix: If True, includes the prefix of the datasource in the download path.
            redownload: Whether to redownload a file if it exists on the filesystem already.

        .. note::
            We don't do any hashsum checks, so if it's possible that the file has been updated,
            set ``redownload`` to True

        Returns:
            Path to the downloaded file
        """

        target_path = self.datasource.default_dataset_location if target is None else Path(target).expanduser()

        # Check if the specified path looks like a file
        # by checking if there's an extension, or it's an already existing file
        n = target_path.name
        target_is_already_file = (target_path.exists() and target_path.is_file()) or (
            "." in n and not n.startswith(".")
        )

        if not target_is_already_file:
            if keep_source_prefix:
                target_path = target_path / self.path_in_repo
            else:
                target_path = target_path / self.path

        download_files([(self.download_url, target_path)], skip_if_exists=not redownload)
        return target_path

    @property
    def blob_cache_location(self):
        return self.datasource.default_dataset_location / ".metadata_blobs"

    def blob_url(self, sha):
        return self.datasource.source.blob_path(sha)

    def get_version_timestamps(
        self,
        fields: Optional[List[str]] = None,
        from_time: Optional[datetime.datetime] = None,
        to_time: Optional[datetime.datetime] = None,
    ) -> List[DatapointHistoryResult]:
        """
        Get the timestamps of all versions of this datapoint, where the specified fields have changed.

        Args:
            fields: List of fields to check for changes. If None, all fields are checked.
            from_time: Only search versions since this time. If None, the start time is unbounded
            to_time: Only search versions until this time. If None, the end time is unbounded

        Returns:
            List of objects with information about the versions.
        """
        return self.datasource.source.client.get_datapoint_history([self], fields, from_time, to_time)


def _get_blob(
    url: Optional[str],
    cache_path: Optional[Path],
    auth,
    cache_on_disk: bool,
    return_blob: bool,
    path_format: Literal["str", "path"] = "path",
) -> Optional[Union[Path, str, bytes]]:
    """
    Args:
        url: url to download the blob from
        cache_path: where the cache for the blob is (laods from it if exists, stores there if it doesn't)
        auth: auth to use for getting the blob
        cache_on_disk: whether to store the downloaded blob on disk. If False we also turn off the cache checking
        return_blob: if True returns the blob of the downloaded data, if False returns the path to the file with it
    """
    if url is None:
        return None
    assert cache_path is not None

    if cache_on_disk and cache_path.exists():
        if return_blob:
            with cache_path.open("rb") as f:
                return f.read()
        else:
            if path_format == "str":
                cache_path = str(cache_path)
            return cache_path

    def get():
        resp = http_request("GET", url, auth=auth)
        if 200 <= resp.status_code < 300:
            return resp.content
        elif resp.status_code == 404:
            raise Exception(f"Blob not found at {url}")
        elif resp.status_code > 400:
            raise RuntimeError(f"Got status code {resp.status_code} from server")
        else:
            raise Exception(f"Non-retrying status code {resp.status_code} returned")

    try:
        for attempt in Retrying(
            retry=retry_if_exception_type(RuntimeError),
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        ):
            with attempt:
                content = get()
    except Exception as e:
        return f"Error while downloading binary blob: {e}"

    if cache_on_disk:
        with cache_path.open("wb") as f:
            f.write(content)

    if return_blob:
        return content
    else:
        if path_format == "str":
            cache_path = str(cache_path)
        return cache_path


def _datetime_from_timestamp(timestamp, utc_offset):
    offset_hours, offset_minutes = map(int, utc_offset.split(":"))
    offset = datetime.timedelta(hours=offset_hours, minutes=offset_minutes)

    tz = datetime.timezone(offset)

    return datetime.datetime.fromtimestamp(timestamp).astimezone(tz)
