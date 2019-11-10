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
                 metrics_path: str = 'metrics.csv',
                 should_log_metrics: bool = True,
                 hparams_path: str = 'params.yml',
                 should_log_hparams: bool = True,
                 should_make_dirs: bool = True,
                 status_hyperparam_name: str = 'status',
                 ):
        """

        :param metrics_path: Where to save the single metrics CSV file.
        :param should_log_metrics: Whether to log metrics at all. Should probably always be True.
        :param hparams_path: Where to save the single hyperparameter YAML file.
        :param should_log_hparams: Whether to log hyperparameters to a file.
            Should be False if you want to work with hyperparameters in a dependency file,
            rather than specifying them using command line arguments.
        :param should_make_dirs: If true, the directory structure required by metrics_path and hparams_path
            will be created. Has no effect if the directory structure already exists.
        :param status_hyperparam_name: The 'status' passed by pytorch_lightning at the end of training
            will be saved as an additional hyperparameter, with this name.
            This can be useful for filtering and searching later on.
            Set to None if you don't want this to happen.
        """
        super(DAGsHubLogger, self).__init__()
        self.metrics_path = metrics_path
        self.should_log_metrics = should_log_metrics
        self.hparams_path = hparams_path
        self.should_log_hparams = should_log_hparams
        self.should_make_dirs = should_make_dirs
        self.status_hyperparam_name = status_hyperparam_name

        self.unsaved_metrics = []
        self.hparams = {}

    @rank_zero_only
    def log_metrics(self, metrics: dict, step_num: int):
        if self.should_log_metrics:
            copy_of_metrics = dict(metrics)
            self.unsaved_metrics.append((copy_of_metrics, self.epoch_milisec(), step_num))

    @staticmethod
    def epoch_milisec():
        microsec_timestamp = datetime.now().timestamp()
        return int(microsec_timestamp * 1000)

    @rank_zero_only
    def log_hyperparams(self, params: Namespace):
        if self.should_log_hparams:
            # Create a copy of the Namespace as a dictionary
            self.hparams = dict(params.__dict__)

    @rank_zero_only
    def save(self):
        if self.should_log_metrics:
            if not hasattr(self, 'metrics_file'):
                self.init_metrics_file()

            for metrics, timestamp, step_num in self.unsaved_metrics:
                for name, value in metrics.items():
                    self.metrics_file.write(f'{name},{value},{timestamp},{step_num}\n')
            self.unsaved_metrics = []

        self.save_hparams()

    def save_hparams(self):
        if self.should_log_hparams:
            self.ensure_dir(self.hparams_path)
            with open(self.hparams_path, 'w') as f:
                yaml.safe_dump(self.hparams, f)

    def init_metrics_file(self):
        self.ensure_dir(self.metrics_path)
        self.metrics_file = open(self.metrics_path, 'w')
        self.metrics_file.write("Name,Value,Timestamp,Step\n")

    def ensure_dir(self, filename: str):
        if self.should_make_dirs:
            dirname = os.path.dirname(filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    @rank_zero_only
    def close(self):
        if hasattr(self, 'metrics_file'):
            self.metrics_file.close()

    @rank_zero_only
    def finalize(self, status: str):
        if self.status_hyperparam_name is not None and self.status_hyperparam_name not in self.hparams:
            self.hparams[self.status_hyperparam_name] = status
        self.save_hparams()
