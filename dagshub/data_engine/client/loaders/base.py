import logging
from types import FunctionType
from typing import List, Union

from pathlib import Path
from multiprocessing import Pool, Process

from dagshub.common.api.repo import PathNotFoundError

logger = logging.getLogger(__name__)


class DagsHubDataset:
    def __init__(
        self,
        query_result,
        metadata_columns: List[str] = [],
        file_columns: List[str] = None,
        strategy: str = "lazy",
        tensorizers: Union[str, List[Union[str, FunctionType]], FunctionType] = "auto",
        savedir: str = None,
        processes: int = 8,
        for_dataloader: bool = False,
    ):
        """
        Initialize a dataset using the specified parameters.

        Args:
        query_result (<dagshub.data_engine.client.models.QueryResult>): The query result containing dataset entries.
        metadata_columns (List[str], optional):
            columns that are returned from the metadata as part of the dataloader.Defaults to [].
        file_columns (List[str], optional): columns with a datapoint metadata that are files. Defaults to None.
        strategy (str, optional): Download strategy - preload|background|lazy. Defaults to "lazy".
        tensorizers (Union[str, List[Union[str, FunctionType]], FunctionType], optional):
            Tensorization strategy - auto|image|<function>. Defaults to "auto".
        savedir (str, optional): Location where the dataset is stored. Defaults to None.
        processes (int, optional): number of parallel processes that download the dataset. Defaults to 8.
        for_dataloader (bool, optional): Whether the dataset is used in a dataloader context. Defaults to False.

        """
        self.metadata_columns = metadata_columns
        self.entries = query_result.entries
        self.tensorizers = [
            lambda x: x,
        ] * (
            len(metadata_columns) + 1
        )  # prevent circular calls
        self.datasource = query_result.datasource
        self.repo = self.datasource.source.repoApi
        self.savedir = Path(savedir) if savedir else self.datasource.default_dataset_location
        self.strategy = strategy
        self.source = self.datasource.source.path.split("://")[0]

        self.datasource_root = Path(self.entries[0].path_in_repo.as_posix()[: -len(self.entries[0].path)])
        self.processes = processes
        self.order = None
        self.file_columns = file_columns or self._get_file_columns()

        self.tensorizers = (
            self._get_tensorizers(tensorizers)
            if type(tensorizers) is str or (type(tensorizers) is list and type(tensorizers[0]) is str)
            else tensorizers
        )

        strategy = strategy.lower()
        if strategy == "preload":
            self.pull()
        elif strategy == "background":
            if for_dataloader:
                return
            Process(target=self.pull).start()
        elif strategy != "lazy":
            logger.warning("Invalid download strategy (none from preload|background|lazy); defaulting to lazy.")

    def __len__(self) -> int:
        return len(self.entries)

    def _get_file_columns(self):
        logger.warning("Manually detecting file columns; this may take a second.")

        res = []
        for column, value in zip(
            self.metadata_columns,
            [self.entries[0].metadata[col] for col in self.metadata_columns],
        ):
            try:
                if self.datasource.source.source_type == self.datasource.source.source_type.REPOSITORY:
                    self.repo.list_path((self.datasource_root / str(value)).as_posix())
                else:
                    self.repo.list_storage_path(
                        (
                            Path("/".join(list(self.datasource.source.path_parts().values())[:2]))
                            / self.datasource_root
                            / str(value)
                        ).as_posix()
                    )
                res.append(column)
            except PathNotFoundError:
                pass
        return res

    def get(self, idx: int) -> list:
        """
        Retrieve data associated with a specific index in the dataset.

        Args:
            idx (int): The index of the data to retrieve.

        Returns:
            list: A list containing data associated with the specified index, including file paths and metadata.
        """
        out = []
        entry = self.entries[idx]

        self._download(entry)
        out.append((self.savedir / entry.path).as_posix())
        for idx, column in enumerate(self.metadata_columns):
            out.append(
                (self.savedir / entry.metadata[column]).as_posix()
                if column in self.file_columns
                else entry.metadata[column]
            )

        return out

    def __getitem__(self, idx: int) -> List[Union["torch.Tensor", "tf.Tensor"]]:  # noqa: F821
        if type(self.tensorizers) is list:
            return [tensorizer(data) for tensorizer, data in zip(self.tensorizers, self.get(idx))]
        else:
            return self.tensorizers(self.get(idx))

    def pull(self) -> None:
        if self.order is not None:
            entries = [self.entries[idx] for idx in self.order]
            self.order = None
        else:
            entries = self.entries

        with Pool(processes=self.processes) as p:
            p.map(self._download, entries, 1)
        logger.info("Dataset download complete!")

    def _download(self, datapoint) -> None:
        paths = [
            datapoint.path,
            *[datapoint.metadata.get(column) for column in self.file_columns],
        ]

        for path in paths:
            (self.savedir / Path(path).parent).mkdir(parents=True, exist_ok=True)
            if not (self.savedir / path).is_file():
                if self.source == "repo":
                    data = self.repo.get_file(f"{self.datasource_root}/{path}")
                else:
                    data = self.repo.get_storage_file(
                        f"{'/'.join(list(self.datasource.source.path_parts().values())[:2])}"
                        f"/{self.datasource_root}/{path}"
                    )

                filepath = self.savedir / path
                with open(filepath, "wb") as file:
                    file.write(data)

    def _get_tensorizers(self, datatypes: Union[str, List[Union[str, FunctionType]]]) -> FunctionType:
        if datatypes in ["auto", "guess"]:  # guess is an easter egg argument
            logger.warning("`tensorizers` set to 'auto'; guessing the datatypes")
            tensorizers = []

            # naive pass
            for idx, entry in enumerate(self.get(0)):
                if not idx or self.metadata_columns[idx - 1] in self.file_columns:
                    extension = entry.split("/")[-1].split(".")[-1]
                    if extension in ["mkv", "mp4"]:
                        tensorizers.append(self.tensorlib.video)
                    elif extension in ["wav", "mp3"]:
                        tensorizers.append(self.tensorlib.audio)
                    elif extension in ["png", "jpg", "jpeg"]:
                        tensorizers.append(self.tensorlib.image)
                    else:
                        raise ValueError(
                            "Unable to automatically detect the datatypes. "
                            "Please manually set a list of tensorizers, either with string arguments image|video|audio,"
                            " or custom tensorizer functions with prototype `<str> -> <torch.Tensor>`."
                        )
                elif type(entry) in [int, float]:
                    tensorizers.append(self.tensorlib.numeric)
                else:
                    raise ValueError(
                        "Unable to automatically tensorize non-numeric metadata. "
                        "Please manually setup a list of tensorizers, either with string arguments image|video|audio, "
                        "or custom tensorizer functions with prototype `<str> -> <torch.Tensor>`."
                    )
            return tensorizers
        elif datatypes in ["image", "audio", "video"]:
            return [
                getattr(self.tensorlib, datatypes),
            ] * (len(self.metadata_columns) + 1)
        elif type(datatypes) is list and len(datatypes) == len(self.metadata_columns) + 1:
            return [getattr(self.tensorlib, datatype) if type(datatype) is str else datatype for datatype in datatypes]
        else:
            raise ValueError(
                "Unable to set tensorizers. "
                "Please ensure the number of selected columns equals the number of tensorizers."
            )
