import logging
from typing import TYPE_CHECKING

from pathlib import Path
from multiprocessing import Pool, Process
from dagshub.common.util import lazy_load
from dagshub.data_engine.client.models import Datapoint

if TYPE_CHECKING:
    import torch

np = lazy_load('numpy')
Image = lazy_load('PIL.Image')
torch = lazy_load('torch')
torchaudio = lazy_load('torchaudio')
torchvision = lazy_load('torchvision')

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

class PyTorchDataset(torch.utils.data.Dataset):
    def __init__(self, query_result, strategy='lazy', tensorizer='auto', savedir=Path.home()/'.dagshub'/'datasets', processes=8):
        """
        query_result: <dagshub.data_engine.client.models.QueryResult>
        strategy: preload|background|lazy; default: lazy
        savedir: location at which the dataset is stored
        processes: number of parallel processes that download the dataset
        tensorizer: auto|image|<function>
        """
        self.tensorizer = lambda x: x # prevent circular calls
        self.savedir = Path(savedir)
        self.entries = query_result.entries
        self.repo = query_result.datasource.source.repoApi
        self.datasource_root = Path(query_result.datasource.source.path[query_result.datasource.source.path.index(query_result.datasource.source.repo) + len(query_result.datasource.source.repo)+1:])

        if type(tensorizer) == str: self._set_tensorizer(tensorizer)
        else: self.tensorizer = tensorizer

        strategy = strategy.lower()
        if strategy == 'preload': self._downloader(processes=processes)
        elif strategy == 'background': Process(target=self._downloader, args=(processes,)).start()
        elif strategy != 'lazy': logger.warning('Invalid download strategy (none from preload|background|lazy); defaulting to lazy.')

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        if type(idx) == Datapoint: entry = idx
        else: entry = self.entries[idx]

        filepath = self.savedir / entry.path
        if not filepath.is_file(): self._download(entry)
        return self.tensorizer(open(filepath, 'rb'))

    def _download(self, entry):
        (self.savedir / Path(entry.path).parent).mkdir(parents=True, exist_ok=True)

        if not (self.savedir / entry.path).is_file():
            data = self.repo.get_file(f'{self.datasource_root}/{entry.path}')
            with open(self.savedir / entry.path, 'wb') as file:
                file.write(data)

    def _downloader(self, processes) -> None:
        with Pool(processes=processes) as p:
            p.map(self._download, self.entries)
        logger.info('Dataset download complete!')

    def _set_tensorizer(self, datatype):
        if datatype in ['auto', 'guess']: # guess is an easter egg argument
            logger.warning('`tensorizer` set to \'auto\'; guessing the datatype')

            ## naive pass
            extension = self.__getitem__(0).name.split('/')[-1].split('.')[-1]
            if extension in ['mkv', 'mp4']: self.tensorizer = TensorizerLib.video
            elif extension in ['wav', 'mp3']: self.tensorizer = TensorizerLib.audio
            elif extension in ['png', 'jpeg']: self.tensorizer = TensorizerLib.image
            else: raise ValueError('Unable to automatically detect the datatype. Please manually set a tensorizer, \
                    either with string arguments image|video|audio, or a custom tokenizer function with prototype `<_io.BufferedReader> -> <Tensor>`.')

        elif datatype in ['image', 'audio', 'video']:
            self.tensorizer = getattr(TensorizerLib, datatype)

class TensorizerLib:
    @staticmethod
    def image(file):
        return torchvision.io.read_image(file.name)

    @staticmethod
    def audio(file):
        return torchaudio.load(file.name)

    @staticmethod
    def video(file):
        return torchvision.io.read_video(file.name)
