import logging
from typing import TYPE_CHECKING

from pathlib import Path
from multiprocessing import Pool, Process
from dagshub.common.util import lazy_load
from dagshub.data_engine.client.models import Datapoint

if TYPE_CHECKING:
    import torch

torch = lazy_load('torch')
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

class PyTorchDataset(torch.utils.data.Dataset):
    def __init__(self, query_result, strategy, savedir=Path.home() / '.dagshub' / 'datasets/', processes=4):
        self.savedir = Path(savedir)
        self.entries = query_result.entries
        self.repo = query_result.datasource.source._api
        self.datasource_root = Path(query_result.datasource.source.path[query_result.datasource.source.path.index(query_result.datasource.source.repo) + len(query_result.datasource.source.repo)+1:])

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
        return open(filepath, 'rb')

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
