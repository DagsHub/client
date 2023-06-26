import logging
from typing import TYPE_CHECKING

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
        strategy="lazy",
        tensorizer="auto",
        savedir=Path.home() / ".dagshub" / "datasets",
        processes=8,
    ):
        """
        query_result: <dagshub.data_engine.client.models.QueryResult>
        strategy: preload|background|lazy; default: lazy
        savedir: location at which the dataset is stored
        processes: number of parallel processes that download the dataset
        tensorizer: auto|image|<function>
        """
        self.tensorizer = lambda x: x  # prevent circular calls
        self.savedir = Path(savedir)
        self.entries = query_result.entries
        self.repo = query_result.datasource.source.repoApi
        self.datasource_root = Path(
            query_result.datasource.source.path[
                query_result.datasource.source.path.index(
                    query_result.datasource.source.repo
                )
                + len(query_result.datasource.source.repo)
                + 1 :
            ]
        )
        self.tensorizer = (
            self._get_tensorizer(tensorizer) if type(tensorizer) == str else tensorizer
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

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        entry = self.entries[idx]

        filepath = self.savedir / entry.path
        if not filepath.is_file():
            self._download(entry)
        return self.tensorizer(open(filepath, "rb"))

    def pull(self, processes) -> None:
        with Pool(processes=processes) as p:
            p.map(self._download, self.entries)
        logger.info("Dataset download complete!")

    def _get_tensorizer(self, datatype):
        if datatype in ["auto", "guess"]:  # guess is an easter egg argument
            logger.warning("`tensorizer` set to 'auto'; guessing the datatype")

            ## naive pass
            extension = self.__getitem__(0).name.split("/")[-1].split(".")[-1]
            if extension in ["mkv", "mp4"]:
                return TorchTensorizers.video
            elif extension in ["wav", "mp3"]:
                self.tensoriszer = TorchTensorizers.audio
            elif extension in ["png", "jpg", "jpeg"]:
                return TorchTensorizers.image
            else:
                raise ValueError(
                    "Unable to automatically detect the datatype. Please manually set a tensorizer, \
                    either with string arguments image|video|audio, or a custom tensorizer function with prototype `<_io.BufferedReader> -> <Tensor>`."
                )

        elif datatype in ["image", "audio", "video"]:
            return getattr(TorchTensorizers, datatype)

    def _download(self, entry):
        (self.savedir / Path(entry.path).parent).mkdir(parents=True, exist_ok=True)

        if not (self.savedir / entry.path).is_file():
            data = self.repo.get_file(f"{self.datasource_root}/{entry.path}")
            with open(self.savedir / entry.path, "wb") as file:
                file.write(data)


class PyTorchDataset(DagsHubDataset):
    pass


class TensorFlowDataset(DagsHubDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signature = tuple(
            tf.TensorSpec.from_tensor(tensor) for tensor in next(self.generator())
        )

    def generator(self):
        for entry in self.entries:
            filepath = self.savedir / entry.path
            if not filepath.is_file():
                self.pull(entry)
            yield (self.tensorizer(open(filepath, "rb")),)

    def _get_tensorizer(self, datatype):
        if datatype in ["auto", "guess"]:  # guess is an easter egg argument
            logger.warning(f"`tensorizer` set to '{datatype}'; guessing the datatype")

            ## naive pass
            extension = self.__getitem__(0).name.split("/")[-1].split(".")[-1]
            if extension in ["mkv", "mp4"]:
                return TensorFlowTensorizers.video
            elif extension in ["wav", "mp3"]:
                return TensorFlowTensorizers.audio
            elif extension in ["png", "jpg", "jpeg"]:
                return TensorFlowTensorizers.image
            else:
                raise ValueError(
                    "Unable to automatically detect the datatype. Please manually set a tensorizer, \
                    either with string arguments image|video|audio, or a custom tensorizer function with prototype `<_io.BufferedReader> -> <torch.Tensor>`."
                )

        elif datatype in ["image", "audio", "video"]:
            return getattr(TensorFlowTensorizers, datatype)


class TensorFlowDataLoader(tf.keras.utils.Sequence):
    def __init__(self, dataset, batch_size=32, shuffle=True, seed=0):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle

        random.seed(seed)
        np.random.seed(seed)

        self.indices = {}
        self.on_epoch_end()

    def __len__(self):
        return self.dataset.__len__() // self.batch_size

    def __getitem__(self, index):
        indices = self.indices[index * self.batch_size : (index + 1) * self.batch_size]
        X = []
        for index in indices:
            X.append(self.dataset.__getitem__(index))
        return tf.stack(X)

    def _get_tensorizer(self, datatype):
        if datatype in ["auto", "guess"]:  # guess is an easter egg argument
            logger.warning(f"`tensorizer` set to '{datatype}'; guessing the datatype")

            ## naive pass
            extension = self.__getitem__(0).name.split("/")[-1].split(".")[-1]
            if extension in ["png", "jpg", "jpeg"]:
                return TensorFlowTensorizers.image
            else:
                raise ValueError(
                    'Unable to automatically detect the datatype. Please manually set a tensorizer, \
                    either with string argument "image", or a custom tensorizer function with prototype `<_io.BufferedReader> -> <tf.Tensor>`.'
                )

        elif datatype in ["image"]:
            return getattr(TensorFlowTensorizers, datatype)
        else:
            raise ValueError("Unsupported tensorizer argument.")

    def on_epoch_end(self):
        self.indices = np.arange(self.dataset.__len__())
        if self.shuffle:
            np.random.shuffle(self.indices)


class TorchTensorizers:
    @staticmethod
    def image(file):
        return torchvision.io.read_image(file.name)

    @staticmethod
    def audio(file):
        return torchaudio.load(file.name)

    @staticmethod
    def video(file):
        return torchvision.io.read_video(file.name)


class TensorFlowTensorizers:
    @staticmethod
    def image(file):
        return tf.convert_to_tensor(tf.keras.utils.load_img(file.name))
