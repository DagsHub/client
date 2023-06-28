import io
import logging
from types import FunctionType
from typing import TYPE_CHECKING, List

import random
from pathlib import Path
from multiprocessing import Pool, Process
from dagshub.common.util import lazy_load

np = lazy_load("numpy")
torch = lazy_load("torch")
tf = lazy_load("tensorflow")
torchaudio = lazy_load("torchaudio")
torchvision = lazy_load("torchvision")
tfds = lazy_load("tensorflow_datasets")
Image = lazy_load("PIL.Image", source_package="pillow")

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)


class DagsHubDataset(torch.utils.data.Dataset):
    def __init__(
        self,
        query_result,
        metadata_columns=[],
        strategy: str = "lazy",
        tensorizers: (str, FunctionType) = "auto",
        savedir: str = None,
        processes: int = 8,
    ):
        """
        query_result: <dagshub.data_engine.client.models.QueryResult>
        strategy: preload|background|lazy; default: lazy
        savedir: location at which the dataset is stored
        processes: number of parallel processes that download the dataset
        tensorizers: auto|image|<function>
        """
        self.metadata_columns = metadata_columns
        self.file_columns = [
            column for column in metadata_columns if column.startswith("file_")
        ]
        self.entries = query_result.entries
        self.tensorizers = [
            lambda x: x,
        ] * (
            len(metadata_columns) + 1
        )  # prevent circular calls
        self.datasource = query_result.datasource
        self.repo = self.datasource.source.repoApi
        self.savedir = self.datasource.default_dataset_location
        self.datasource_root = Path(
            self.datasource.source.path[
                self.datasource.source.path.index(self.datasource.source.repo)
                + len(self.datasource.source.repo)
                + 1 :
            ]
        )

        from dagshub.data_engine.client.models import (
            Datapoint,
        )  # prevent circular imports

        self.datapoint_class = Datapoint

        self.tensorizers = (
            self._get_tensorizers(tensorizers)
            if type(tensorizers) == str or type(tensorizers[0]) == str
            else tensorizers
        )

        strategy = strategy.lower()
        if strategy == "preload":
            self.pull(processes=processes)
        elif strategy == "background":
            Process(target=self.pull, args=(processes,)).start()
        elif strategy != "lazy":
            logger.warning(
                "Invalid download strategy (none from preload|background|lazy); defaulting to lazy."
            )

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, idx: int) -> (List[torch.Tensor], List[tf.Tensor]):
        out = []
        entry = self.entries[idx]

        out.append(self._get_file(entry))
        for idx, column in enumerate(self.metadata_columns):
            out.append(
                self._get_file(self.datapoint_class("", entry.metadata[column], {}))
                if column in self.file_columns
                else entry.metadata[column]
            )

        return [tensorizer(data) for tensorizer, data in zip(self.tensorizers, out)]

    def pull(self, processes: int) -> None:
        with Pool(processes=processes) as p:
            p.map(self._download, self.entries)
        logger.info("Dataset download complete!")

    def _get_file(self, entry) -> io.BufferedReader:
        filepath = self.savedir / entry.path
        if not filepath.is_file():
            self._download(entry, is_subentry=entry.metadata.get('subentry', False))
        return open(filepath, "rb")

    def _download(self, datapoint, is_subentry=False) -> None:
        if is_subentry: entries = [datapoint,]
        else:
            entries = [
                 datapoint,
                 *[
                     self.datapoint_class('', datapoint.metadata.get(column), {'subentry': True})
                     for column in self.file_columns
                 ],
             ]

        for entry in entries:
            (self.savedir / Path(entry.path).parent).mkdir(parents=True, exist_ok=True)
            if not (self.savedir / entry.path).is_file():
                data = self.repo.get_file(f"{self.datasource_root}/{entry.path}")
                filepath = self.savedir / entry.path
                with open(filepath, "wb") as file:
                    file.write(data)

    def _get_tensorizers(
        self, datatypes: (str, List[str], List[FunctionType])
    ) -> FunctionType:
        if datatypes in ["auto", "guess"]:  # guess is an easter egg argument
            logger.warning("`tensorizers` set to 'auto'; guessing the datatypes")
            tensorizers = []

            ## naive pass
            for idx, entry in enumerate(self[0]):
                if not idx or self.metadata_columns[idx - 1] in self.file_columns:
                    extension = entry.name.split("/")[-1].split(".")[-1]
                    if extension in ["mkv", "mp4"]:
                        tensorizers.append(self.tensorlib.video)
                    elif extension in ["wav", "mp3"]:
                        tensorizers.append(self.tensorlib.audio)
                    elif extension in ["png", "jpg", "jpeg"]:
                        tensorizers.append(self.tensorlib.image)
                    else:
                        raise ValueError(
                            "Unable to automatically detect the datatypes. Please manually set a list of tensorizers, \
                                        either with string arguments image|video|audio, or custom tensorizer functions with prototype `<io.BufferedReader> -> <torch.Tensor>`."
                        )
                elif type(entry) in [int, float]:
                    tensorizers.append(self.tensorlib.numeric)
                else:
                    raise ValueError(
                        "Unable to automatically tensorize non-numeric metadata. Please menually setup a list of tensorizers, either with string arguments image|video|audio, or custom tensorizer functions with prototype `<io.BufferedReader> -> <torch.Tensor>`."
                    )
            return tensorizers
        elif datatypes in ["image", "audio", "video"]:
            return [
                getattr(self.tensorlib, datatypes),
            ] * len(self.metadata_columns) + 1
        elif len(datatypes) == len(self.metadata_columns):
            return [
                getattr(self.tensorlib, datatype) if type(datatype) == str else datatype
                for datatype in datatypes
            ]
        else:
            raise ValueError(
                "Unable to set tensorizers. Please ensure the number of selected columns equals the number of tensorizers."
            )


class PyTorchDataset(DagsHubDataset):
    def __init__(self, *args, **kwargs):
        self.tensorlib = TorchTensorizers
        super().__init__(*args, **kwargs)


class TensorFlowDataset(DagsHubDataset):
    def __init__(self, *args, **kwargs):
        self.tensorlib = TensorFlowTensorizers
        super().__init__(*args, **kwargs)
        self.signature = tuple(
            tf.TensorSpec.from_tensor(tensor) for tensor in next(self.generator())
        )

    def generator(self):
        for idx in range(len(self)):
            yield self[idx]
        # for entry in self.entries:
        #     filepath = self.savedir / entry.path
        #     if not filepath.is_file():
        #         self.pull(entry)
        #     yield (self.tensorizers(open(filepath, "rb")),)


class TensorFlowDataLoader(tf.keras.utils.Sequence):
    def __init__(self, dataset, batch_size=1, shuffle=True, seed=None):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle

        if seed:
            random.seed(seed)
            np.random.seed(seed)

        self.indices = {}
        self.on_epoch_end()

    def __len__(self) -> int:
        return self.dataset.__len__() // self.batch_size

    def __getitem__(self, index: int) -> tf.Tensor:
        indices = self.indices[index * self.batch_size : (index + 1) * self.batch_size]
        X = []
        for index in indices:
            X.append(self.dataset.__getitem__(index))
        return tf.stack(X)

    def on_epoch_end(self) -> None:
        self.indices = np.arange(self.dataset.__len__())
        if self.shuffle:
            np.random.shuffle(self.indices)


class TorchTensorizers:
    @staticmethod
    def image(file: io.BufferedReader) -> torch.Tensor:
        return torchvision.io.read_image(file.name).type(torch.float)

    @staticmethod
    def audio(file: io.BufferedReader) -> torch.Tensor:
        return torchaudio.load(file.name).type(torch.float)

    @staticmethod
    def video(file: io.BufferedReader) -> torch.Tensor:
        return torchvision.io.read_video(file.name).type(torch.float)

    @staticmethod
    def numeric(num: (float, int)) -> torch.Tensor:
        return torch.tensor(num, dtype=torch.float)


class TensorFlowTensorizers:
    @staticmethod
    def image(file: io.BufferedReader) -> tf.Tensor:
        return tf.convert_to_tensor(tf.keras.utils.load_img(file.name))
