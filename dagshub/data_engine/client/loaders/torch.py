from multiprocessing import Process
from typing import TYPE_CHECKING, Union
from dagshub.common.util import lazy_load
from dagshub.data_engine.client.loaders.base import DagsHubDataset

torch = lazy_load("torch")
torchaudio = lazy_load("torchaudio")
torchvision = lazy_load("torchvision")

if TYPE_CHECKING:
    import torch


class PyTorchDataset(DagsHubDataset, torch.utils.data.Dataset):
    def __init__(self, *args, **kwargs):
        self.tensorlib = Tensorizers
        super().__init__(*args, **kwargs)
        self.type = "torch"


class PyTorchDataLoader(torch.utils.data.DataLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset.order = list(self.sampler)
        if self.dataset.strategy == "background":
            Process(target=self.dataset.pull).start()


class Tensorizers:
    @staticmethod
    def image(filepath: str) -> torch.Tensor:
        return torchvision.io.read_image(filepath).type(torch.float)

    @staticmethod
    def audio(filepath: str) -> torch.Tensor:
        return torchaudio.load(filepath).type(torch.float)

    @staticmethod
    def video(filepath: str) -> torch.Tensor:
        return torchvision.io.read_video(filepath).type(torch.float)

    @staticmethod
    def numeric(num: Union[float, int]) -> torch.Tensor:
        return torch.tensor(num, dtype=torch.float)
