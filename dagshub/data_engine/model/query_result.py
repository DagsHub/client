import inspect
import logging
import multiprocessing.pool
from dataclasses import field, dataclass
from itertools import repeat
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Union

import rich.progress

from dagshub.common import config
from dagshub.common.analytics import send_analytics_event
from dagshub.common.download import download_files
from dagshub.common.helpers import sizeof_fmt, prompt_user
from dagshub.common.rich_util import get_rich_progress
from dagshub.common.util import lazy_load
from dagshub.data_engine.annotation.voxel_conversion import (
    add_voxel_annotations,
    add_ls_annotations,
)
from dagshub.data_engine.client.models import DatasourceType
from dagshub.data_engine.model.datapoint import Datapoint, _get_blob
from dagshub.data_engine.client.loaders.base import DagsHubDataset
from dagshub.data_engine.voxel_plugin_server.utils import set_voxel_envvars
from dagshub.data_engine.dtypes import MetadataFieldType

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource
    import fiftyone as fo
    import dagshub.data_engine.voxel_plugin_server.server as plugin_server_module
else:
    plugin_server_module = lazy_load("dagshub.data_engine.voxel_plugin_server.server")
    fo = lazy_load("fiftyone")
    tf = lazy_load("tensorflow")

logger = logging.getLogger(__name__)


class VisualizeError(Exception):
    """:meta private:"""
    pass


@dataclass
class QueryResult:
    """
    Result of executing a query on a :class:`.Datasource`.

    You can iterate over this object to get the :class:`datapoints <.Datapoint>`::

        res = ds.head()
        for dp in res:
            print(dp.path_in_repo)

    """
    _entries: List[Datapoint]
    datasource: "Datasource"
    _datapoint_path_lookup: Dict[str, Datapoint] = field(init=False)

    def __post_init__(self):
        self._refresh_lookups()

    @property
    def entries(self):
        """
        list(Datapoint): Datapoints contained in this QueryResult
        """
        return self._entries

    @entries.setter
    def entries(self, value: List[Datapoint]):
        self._entries = value
        self._refresh_lookups()

    def _refresh_lookups(self):
        self._datapoint_path_lookup = {}
        for e in self.entries:
            self._datapoint_path_lookup[e.path] = e

    @property
    def dataframe(self):
        """
        Represent the contents of this QueryResult as a
        `pandas.DataFrame <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_.

        The created dataframe has a copy of the QueryResult's data.
        """
        import pandas as pd

        metadata_keys = set()
        for e in self.entries:
            metadata_keys.update(e.metadata.keys())

        metadata_keys = list(sorted(metadata_keys))
        return pd.DataFrame.from_records([dp.to_dict(metadata_keys) for dp in self.entries])

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        """You can iterate over a QueryResult to get containing datapoints"""
        return self.entries.__iter__()

    def __repr__(self):
        return f"QueryResult of datasource {self.datasource.source.name} with {len(self.entries)} datapoint(s)"

    @staticmethod
    def from_gql_query(query_resp: Dict[str, Any], datasource: "Datasource") -> "QueryResult":
        if "edges" not in query_resp:
            return QueryResult([], datasource)
        if query_resp["edges"] is None:
            return QueryResult([], datasource)
        return QueryResult(
            [Datapoint.from_gql_edge(edge, datasource) for edge in query_resp["edges"]],
            datasource,
        )

    def as_ml_dataset(self, flavor: str, **kwargs):
        """
        Convert the QueryResult into a dataset for a machine learning framework

        Args:
            flavor: Either of:

                - ``"torch"``: returns a \
                `torch.utils.data.Dataset <https://pytorch.org/docs/stable/data.html#torch.utils.data.Dataset>`_
                - ``"tensorflow"``: returns a \
                `tf.data.Dataset <https://www.tensorflow.org/api_docs/python/tf/data/Dataset>`_


        Keyword Args:
            metadata_columns (list(str)): which fields to use in the dataset.
            strategy (str): Datapoint file loading strategy. Possible values:

                - ``"preload"`` - Download all datapoints before returning the dataset.
                - ``"background"`` - Start downloading the datapoints in the background. \
                    If an undownloaded datapoint is accessed, it gets downloaded.
                - ``"lazy"`` (default) - Download each datapoint as it is being accessed by the dataset.

            savedir (str|Path): Where to store the datapoint files. Default is :func:`datasource's default location \
                <dagshub.data_engine.model.datasource.Datasource.default_dataset_location>`
            processes (int): number of parallel processes to download the datapoints with. Default is 8.
            tensorizers: How to transform the datapoint file/metadata into tensors. Possible values:

                - ``"auto"`` - try to guess the tensorizers for every field.\
                    For files the tensorizer will be the determined by the first file's extension.
                - ``"image"`` | ``"audio"`` - tensorize all fields according to this type
                - List of tensorizers. First is the tensorizer for the datapoint file and then \
                    a tensorizer for each of the metadata fields. Tensorizer can either be strings\
                     ``"image"``, ``"audio"``, ``"numeric"``, or your own function that receives the\
                     metadata value of the field and turns it into a tensor.
        """
        flavor = flavor.lower()
        if flavor == "torch":
            from dagshub.data_engine.client.loaders.torch import PyTorchDataset

            return PyTorchDataset(self, **kwargs)
        elif flavor == "tensorflow":
            from dagshub.data_engine.client.loaders.tf import TensorFlowDataset

            ds_builder = TensorFlowDataset(self, **kwargs)
            ds = tf.data.Dataset.from_generator(ds_builder.generator, output_signature=ds_builder.signature)
            ds.__len__ = lambda: ds_builder.__len__()
            ds.__getitem__ = ds_builder.__getitem__
            ds.builder = ds_builder
            ds.type = "tensorflow"
            return ds
        else:
            raise ValueError("supported flavors are torch|tensorflow")

    def as_ml_dataloader(self, flavor, **kwargs):
        """
        Convert the QueryResult into a dataloader for a machine learning framework

        Args:
            flavor: Either of:

                - ``"torch"``: returns a \
                `torch.utils.data.DataLoader <https://pytorch.org/docs/stable/data.html#torch.utils.data.DataLoader>`_
                - ``"tensorflow"``: returns a \
                `tf.keras.utils.Sequence <https://www.tensorflow.org/api_docs/python/tf/keras/utils/Sequence>`_

        Kwargs are the same as :func:`as_ml_dataset()`.
        """

        send_analytics_event(
            "Client_DataEngine_DataLoaderInitialized",
            repo=self.datasource.source.repoApi,
        )

        def keypairs(keys):
            return {key: kwargs[key] for key in keys}

        if type(flavor) is not str:
            if flavor.type == "torch":
                from dagshub.data_engine.client.loaders.torch import PyTorchDataLoader

                return PyTorchDataLoader(flavor, **kwargs)
            elif flavor.type == "tensorflow":
                from dagshub.data_engine.client.loaders.tf import TensorFlowDataLoader

                return TensorFlowDataLoader(flavor, **kwargs)

        kwargs["for_dataloader"] = True
        dataset_kwargs = set(list(inspect.signature(DagsHubDataset).parameters.keys())[1:])
        global_kwargs = set(kwargs.keys())
        flavor = flavor.lower() if type(flavor) is str else flavor
        if flavor == "torch":
            from dagshub.data_engine.client.loaders.torch import PyTorchDataLoader

            return PyTorchDataLoader(
                self.as_ml_dataset(flavor, **keypairs(global_kwargs.intersection(dataset_kwargs))),
                **keypairs(global_kwargs - dataset_kwargs),
            )
        elif flavor == "tensorflow":
            from dagshub.data_engine.client.loaders.tf import TensorFlowDataLoader

            return TensorFlowDataLoader(
                self.as_ml_dataset(
                    flavor,
                    **keypairs(global_kwargs.intersection(dataset_kwargs)),
                ),
                **keypairs(global_kwargs - dataset_kwargs),
            )
        else:
            raise ValueError("supported flavors are torch|tensorflow|<torch.utils.data.Dataset>|<tf.data.Dataset>")

    def __getitem__(self, item: Union[str, int, slice]):
        """
        Gets datapoint by its path (string) or by its index in the result (or slice)
        """
        if type(item) is str:
            return self._datapoint_path_lookup[item]
        elif type(item) is int:
            return self.entries[item]
        elif type(item) is slice:
            return QueryResult(_entries=self.entries[item], datasource=self.datasource)
        else:
            raise ValueError(
                f"Can't lookup datapoint using value {item} of type {type(item)}, "
                f"needs to be either int or str or slice"
            )

    def get_blob_fields(
        self, *fields: str, load_into_memory=False, cache_on_disk=True, num_proc: int = config.download_threads
    ) -> "QueryResult":
        """
        Downloads data from blob fields

        Args:
            fields: list of binary fields to download blobs for. If empty, download all blob fields.
            load_into_memory: Whether to load the blobs into the datapoints, or just store them on disk


                If True: the datapoints' specified fields will contain the blob data

                If False: the datapoints' specified fields will contain Path objects to the file of the downloaded blob
            cache_on_disk: Whether to cache the blobs on disk or not (valid only if load_into_memory is set to True)
                Cache location is ``~/dagshub/datasets/<repo>/<datasource_id>/.metadata_blobs/``
            num_proc: number of download threads
        """
        send_analytics_event("Client_DataEngine_downloadBlobs", repo=self.datasource.source.repoApi)
        if not load_into_memory:
            assert cache_on_disk

        # If no fields are specified, include all blob fields from self.datasource.fields
        if not fields:
            fields = [field.name for field in self.datasource.fields if field.valueType == MetadataFieldType.BLOB]

        for fld in fields:
            logger.info(f"Downloading metadata for field {fld} with {num_proc} processes")
            cache_location = self.datasource.default_dataset_location / ".metadata_blobs"

            if cache_on_disk:
                cache_location.mkdir(parents=True, exist_ok=True)

            blob_urls = list(map(lambda dp: dp._extract_blob_url_and_path(fld), self.entries))
            auth = self.datasource.source.repoApi.auth
            func_args = zip(
                map(lambda bu: bu[0], blob_urls),
                map(lambda bu: bu[1], blob_urls),
                repeat(auth),
                repeat(cache_on_disk),
                repeat(load_into_memory),
            )
            with multiprocessing.pool.ThreadPool(num_proc) as pool:
                res = pool.starmap(_get_blob, func_args)

            for dp, binary_val_or_path in zip(self.entries, res):
                if binary_val_or_path is None:
                    continue
                dp.metadata[fld] = binary_val_or_path

        return self

    def download_binary_columns(
        self, *columns: str, load_into_memory=True, cache_on_disk=True, num_proc: int = 32
    ) -> "QueryResult":
        """
        deprecated: Use get_blob_fields instead.

        :meta private:
        """
        return self.get_blob_fields(
            *columns, load_into_memory=load_into_memory, cache_on_disk=cache_on_disk, num_proc=num_proc
        )

    def download_files(
        self,
        target_dir: Optional[Union[str, PathLike]] = None,
        keep_source_prefix=True,
        redownload=False,
        path_field: Optional[str] = None,
    ) -> PathLike:
        """
        Downloads the datapoints to the ``target_dir`` directory

        Args:
            target_dir: Where to download the files. Defaults to \
                :func:`datasource's default location \
                <dagshub.data_engine.model.datasource.Datasource.default_dataset_location>`
            keep_source_prefix: If True, includes the prefix of the datasource in the download path.
            redownload: Whether to redownload a file if it exists on the filesystem already.\
                We don't do any hashsum checks, so if it's possible that the file has been updated, set to True
            path_field: Set this to the name of the field with the file's path\
                if you want to download files from a field other than the datapoint's path.

        .. note::
            For ``path_field`` the path in the field still needs to be in the same repo
            and have the same format as the path of the datapoint, including not having the prefix.
            For now, you can't download arbitrary paths/urls.

        Returns:
            Path to the directory with the downloaded files
        """

        target_path = self.datasource.default_dataset_location if target_dir is None else Path(target_dir).expanduser()
        logger.warning(f"Downloading {len(self.entries)} files to {str(target_path)}")

        if self.datasource.source.source_type == DatasourceType.BUCKET:
            send_analytics_event(
                "Client_DataEngine_downloadDatapointsFromBucket",
                repo=self.datasource.source.repoApi,
            )
        else:
            send_analytics_event(
                "Client_DataEngine_downloadDatapoints",
                repo=self.datasource.source.repoApi,
            )

        def dp_path(dp: Datapoint):
            if path_field is not None:
                path_val = dp.metadata.get(path_field)
                if path_val is None:
                    return None
            else:
                path_val = dp.path

            if keep_source_prefix:
                return target_path / self.datasource.source.source_prefix / path_val
            else:
                return target_path / path_val

        def dp_url(dp: Datapoint):
            if path_field is not None:
                path_val = dp.metadata.get(path_field)
                if path_val is None:
                    return None
                return self.datasource.source.raw_path(path_val)
            else:
                return dp.download_url

        download_args = [(dp_url(dp), dp_path(dp)) for dp in self.entries if dp_path(dp) is not None]

        download_files(download_args, skip_if_exists=not redownload)
        return target_path

    def to_voxel51_dataset(self, **kwargs) -> "fo.Dataset":
        """
        Creates a voxel51 dataset that can be used with\
        `fo.launch_app()
        <https://docs.voxel51.com/api/fiftyone.core.session.html?highlight=launch_app#fiftyone.core.session.launch_app>`_
        to visualize it.

        Keyword Args:
            name (str): Name of the dataset. Default is the name of the datasource.
            force_download (bool): Download the dataset even if the size of the files is bigger than 100MB.\
                Default is False
            files_location (str|PathLike): path to the location where to download the local files.
                Default is :func:`datasource's default location \
                <dagshub.data_engine.model.datasource.Datasource.default_dataset_location>`
            redownload (bool): Redownload files, replacing the ones that might exist on the filesystem.\
                Default is False.
            voxel_annotations (List[str]) : List of fields from which to load voxel annotations serialized with
                                        `to_json()`. This will override the labelstudio annotations

        :rtype: `fo.Dataset <https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.Dataset>`_
        """
        if len(self.entries) == 0:
            raise VisualizeError("No datapoints to visualize")
        logger.info("Migrating dataset to voxel51")
        name = kwargs.get("name", self.datasource.source.name)
        force_download = kwargs.get("force_download", False)
        # TODO: don't override samples in existing one
        if fo.dataset_exists(name):
            ds: fo.Dataset = fo.load_dataset(name)
        else:
            ds: fo.Dataset = fo.Dataset(name)
        # ds.persistent = True

        dataset_location = Path(kwargs.get("files_location", self.datasource.default_dataset_location))
        dataset_location.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading files...")

        if "voxel_annotations" in kwargs:
            annotation_fields = kwargs["voxel_annotations"]
            label_func = add_voxel_annotations
        else:
            annotation_fields = self.datasource.annotation_fields
            label_func = add_ls_annotations

        # Load the annotation fields
        self.download_binary_columns(*annotation_fields)

        if not force_download:
            self._check_downloaded_dataset_size()

        redownload = kwargs.get("redownload", False)
        self.download_files(self.datasource.default_dataset_location, redownload=redownload)

        progress = get_rich_progress(rich.progress.MofNCompleteColumn())
        task = progress.add_task("Generating voxel samples...", total=len(self.entries))

        samples: List["fo.Sample"] = []

        with progress:
            for datapoint in self.entries:
                filepath = self.datasource.default_dataset_location / datapoint.path_in_repo
                sample = fo.Sample(filepath=filepath)
                sample["dagshub_download_url"] = datapoint.download_url
                sample["datapoint_id"] = datapoint.datapoint_id
                sample["datapoint_path"] = datapoint.path
                label_func(sample, datapoint, *annotation_fields)
                for k, v in datapoint.metadata.items():
                    # TODO: more filtering here, not all fields should be showing up in voxel
                    if k in annotation_fields:
                        continue
                    if type(v) is not bytes:
                        sample[k] = v
                samples.append(sample)
                progress.update(task, advance=1, refresh=True)

        ds.merge_samples(samples)
        return ds

    def _check_downloaded_dataset_size(self):
        download_size_prompt_threshold = 100 * (2 ** 20)  # 100 Megabytes
        dp_size = self._calculate_datapoint_size()
        if dp_size is not None and dp_size > download_size_prompt_threshold:
            prompt = f"You're about to download {sizeof_fmt(dp_size)} of images locally."
            should_download = prompt_user(prompt)
            if not should_download:
                msg = "Downloading voxel dataset cancelled"
                logger.warning(msg)
                raise RuntimeError(msg)

    def _calculate_datapoint_size(self) -> Optional[int]:
        sum_size = 0
        has_sum_field = False
        all_have_sum_field = True
        size_field = "size"
        for dp in self.entries:
            if size_field in dp.metadata:
                has_sum_field = True
                sum_size += dp.metadata[size_field]
            else:
                all_have_sum_field = False
        if not has_sum_field:
            logger.warning("None of the datapoints had a size field, can't calculate size of the downloading dataset")
            return None
        if not all_have_sum_field:
            logger.warning("Not every datapoint has a size field, size calculations might be wrong")
        return sum_size

    def visualize(self, **kwargs):
        """
        Visualize this QueryResult with Voxel51.

        This function calls :func:`to_voxel51_dataset`, passing to it the keyword arguments,
        and launches a fiftyone session showing the dataset.

        Additionally, this function adds a DagsHub plugin into Voxel51 that you can use for additional interactions
        with the datasource from within the voxel environment.

        Returns the session object that you can ``wait()`` if you are using it\
        outside a notebook and need to not close the script immediately::

            session = ds.all().visualize()
            session.wait(-1)
        """
        set_voxel_envvars()

        send_analytics_event("Client_DataEngine_VizualizeResults", repo=self.datasource.source.repoApi)

        ds = self.to_voxel51_dataset(**kwargs)

        sess = fo.launch_app(ds)
        # Launch the server for plugin interaction
        plugin_server_module.run_plugin_server(sess, self.datasource, self.datasource.source.revision)

        return sess

    def annotate(self, open_project=True,
                 ignore_warning=True,
                 fields_to_embed=None,
                 fields_to_exclude=None
                 ) -> Optional[str]:
        """
        Sends all the datapoints returned in this QueryResult to be annotated in Label Studio on DagsHub.

        Args:
            open_project: Automatically open the Label Studio project in the browser
            ignore_warning: Suppress the prompt-warning if you try to annotate too many datapoints at once.
            fields_to_embed: list of meta-data columns that will show up in Label Studio UI.
             if not specified all will be displayed.
            fields_to_exclude: list of meta-data columns that will not show up in Label Studio UI
        Returns:
            The URL of the created Label Studio workspace
        """
        send_analytics_event("Client_DataEngine_SentToAnnotation", repo=self.datasource.source.repoApi)

        return self.datasource.send_datapoints_to_annotation(
            self.entries, open_project=open_project, ignore_warning=ignore_warning, fields_to_exclude=fields_to_exclude,
            fields_to_embed=fields_to_embed
        )
