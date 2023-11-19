from multiprocessing import Process
from dagshub.common.util import lazy_load
from typing import TYPE_CHECKING, Union, Any
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


class _BaseDataLoaderIter:
    def __next__(self) -> Any:
        return self.post_hook(super().__next__())


class _SingleProcessDataLoaderIter(_BaseDataLoaderIter, torch.utils.data.dataloader._SingleProcessDataLoaderIter):
    def __init__(self, *args, post_hook, **kwargs):
        self.post_hook = post_hook
        super().__init__(*args, **kwargs)


class _MultiProcessingDataLoaderIter(_BaseDataLoaderIter, torch.utils.data.dataloader._MultiProcessingDataLoaderIter):
    def __init__(self, *args, post_hook, **kwargs):
        self.post_hook = post_hook
        super().__init__(*args, **kwargs)


class PyTorchDataLoader(torch.utils.data.DataLoader):
    def __init__(self, *args, post_hook=lambda x: x, **kwargs):
        super().__init__(*args, **kwargs)
        self.post_hook = post_hook
        self.dataset.order = list(self.sampler)
        if self.dataset.strategy == "background":
            Process(target=self.dataset.pull).start()

    def _get_iterator(self) -> "_BaseDataLoaderIter":
        if self.num_workers == 0:
            return _SingleProcessDataLoaderIter(self, post_hook=self.post_hook)
        else:
            self.check_worker_number_rationality()
            return _MultiProcessingDataLoaderIter(self, post_hook=self.post_hook)


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
