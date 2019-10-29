import os
from argparse import Namespace
from datetime import datetime
from typing import TextIO

import pytorch_lightning
import yaml
from pytorch_lightning.logging import rank_zero_only


class DAGsHubLogger(pytorch_lightning.logging.LightningLoggerBase):

    metrics_file: TextIO

    def __init__(self,
                 metrics_path: str = 'lightning_logs/metrics.csv',
                 hparams_path: str = 'lightning_logs/params.yml',
                 make_dirs: bool = True):
        """
        :param metrics_path: Where to save the single metrics CSV file.
        :param hparams_path: Where to save the single hyperparameter YAML file.
        :param make_dirs: If true, the directory structure required by <b>metrics_path</b> and :param hparams_path
            will be created. has no effect if the directory structure already exists.
        """
        super(DAGsHubLogger, self).__init__()
        self.hparams_path = hparams_path
        self.metrics_path = metrics_path
        self.make_dirs = make_dirs
        self.first_metrics_save = True
        self.unsaved_metrics = []
        self.hparams = {}

    @rank_zero_only
    def log_metrics(self, metrics: dict, step_num: int):
        copy_of_metrics = dict(metrics)
        self.unsaved_metrics.append((copy_of_metrics, self.epoch_milisec(), step_num))

    @staticmethod
    def epoch_milisec():
        microsec_timestamp = datetime.now().timestamp()
        return int(microsec_timestamp * 1000)

    @rank_zero_only
    def log_hyperparams(self, params: Namespace):
        # Create a copy of the Namespace as a dictionary
        self.hparams = dict(params.__dict__)

    @rank_zero_only
    def save(self):
        if self.first_metrics_save:
            self.init_metrics_file()

        for metrics, timestamp, step_num in self.unsaved_metrics:
            for name, value in metrics.items():
                self.metrics_file.write(f'{name},{value},{timestamp},{step_num}\n')
        self.unsaved_metrics = []

    def init_metrics_file(self):
        self.first_metrics_save = False
        self.ensure_dir(self.metrics_path)
        self.metrics_file = open(self.metrics_path, 'w')
        self.metrics_file.write("Name,Value,Timestamp,Step\n")

    def ensure_dir(self, filename: str):
        if self.make_dirs:
            dirname = os.path.dirname(filename)
            os.makedirs(dirname, exist_ok=True)

    @rank_zero_only
    def close(self):
        self.metrics_file.close()

    @rank_zero_only
    def finalize(self, status: str):
        self.ensure_dir(self.hparams_path)
        if 'status' not in self.hparams:
            self.hparams['status'] = status
        with open(self.hparams_path, 'w') as f:
            yaml.safe_dump(self.hparams, f)
