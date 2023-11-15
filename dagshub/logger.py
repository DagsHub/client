import os
from contextlib import contextmanager
from datetime import datetime
from typing import TextIO, ContextManager, Any, Dict

import yaml
import csv


class DAGsHubLogger:
    """
    A plain Python logger for your metrics and hyperparameters.
    The saved file format is plain and open - CSV for metrics files, YAML for hyperparameters.
    You can use this logger manually, or use one of our integrations with high-level libraries
    like Keras or pytorch-lightning.
    """

    metrics_file: TextIO
    metrics_csv_writer: Any
    hparams: Dict[str, Any]

    def __init__(
        self,
        metrics_path: str = "metrics.csv",
        should_log_metrics: bool = True,
        hparams_path: str = "params.yml",
        should_log_hparams: bool = True,
        should_make_dirs: bool = True,
        eager_logging: bool = True,
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
        :param eager_logging: If true, the logged metrics and hyperparams will be saved to file immediately.
            If false, the logger will wait until save() is called, and until then, will hold metrics and hyperparams
            in memory. Watch out not to run out of memory!
        """
        self.metrics_path = metrics_path
        self.should_log_metrics = should_log_metrics
        self.hparams_path = hparams_path
        self.should_log_hparams = should_log_hparams
        self.should_make_dirs = should_make_dirs
        self.eager_logging = eager_logging

        self.unsaved_metrics = []
        self.hparams = {}

        if eager_logging:
            self.save()

    def log_metrics(self, metrics: Dict[str, Any] = None, step_num: int = 1, **kwargs):
        if self.should_log_metrics:
            copy_of_metrics = dict(metrics or {})
            copy_of_metrics.update(kwargs)
            self.unsaved_metrics.append((copy_of_metrics, self.epoch_milisec(), step_num))
            if self.eager_logging:
                self.save_metrics()

    @staticmethod
    def epoch_milisec():
        microsec_timestamp = datetime.now().timestamp()
        return int(microsec_timestamp * 1000)

    def log_hyperparams(self, params: Dict[str, Any] = None, **kwargs):
        if self.should_log_hparams:
            self.hparams.update(self.normalize_dictionary_values(params or {}))
            self.hparams.update(self.normalize_dictionary_values(kwargs or {}))
            if self.eager_logging:
                self.save_hparams()

    def save(self):
        self.save_metrics()
        self.save_hparams()

    def save_metrics(self):
        if self.should_log_metrics:
            if not hasattr(self, "metrics_file"):
                self.init_metrics_file()

            for metrics, timestamp, step_num in self.unsaved_metrics:
                for name, value in metrics.items():
                    self.metrics_csv_writer.writerow([name, value, timestamp, step_num])
            self.unsaved_metrics = []

    def save_hparams(self):
        if self.should_log_hparams:
            self.ensure_dir(self.hparams_path)
            with open(self.hparams_path, "w") as f:
                yaml.safe_dump(self.hparams, f)

    @staticmethod
    def normalize_dictionary_values(dictionary):
        def normalize_dict_deep(dictionary):
            if dictionary is None:
                return None

            new_dict = {}
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    new_dict[key] = normalize_dict_deep(value)
                    continue
                new_dict[key] = value if value is None or type(value) in [int, float, bool] else str(value)

            return new_dict

        return normalize_dict_deep(dictionary)

    def init_metrics_file(self):
        self.ensure_dir(self.metrics_path)
        self.metrics_file = open(self.metrics_path, "w", newline="")  # newline='' required for csv writer
        self.metrics_file.write("Name,Value,Timestamp,Step\n")
        self.metrics_csv_writer = csv.writer(self.metrics_file, quoting=csv.QUOTE_NONNUMERIC)

    def ensure_dir(self, filename: str):
        if self.should_make_dirs:
            dirname = os.path.dirname(filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    def close(self):
        if hasattr(self, "metrics_file"):
            self.metrics_file.close()


@contextmanager
def dagshub_logger(
    metrics_path: str = "metrics.csv",
    should_log_metrics: bool = True,
    hparams_path: str = "params.yml",
    should_log_hparams: bool = True,
    should_make_dirs: bool = True,
    eager_logging: bool = True,
) -> ContextManager[DAGsHubLogger]:
    """
    Example usage:

    with dagshub_logger() as logger:
        logger.log_hyperparams( {'lr': 1e-3, 'num_layers': 42} )\n
        logger.log_metrics( {'loss': 3.14, 'val_loss': 6.28} )\n
        logger.log_metrics(acc=0.999)\n


    :param metrics_path: Where to save the single metrics CSV file.
    :param should_log_metrics: Whether to log metrics at all. Should probably always be True.
    :param hparams_path: Where to save the single hyperparameter YAML file.
    :param should_log_hparams: Whether to log hyperparameters to a file.
        Should be False if you want to work with hyperparameters in a dependency file,
        rather than specifying them using command line arguments.
    :param should_make_dirs: If true, the directory structure required by metrics_path and hparams_path
        will be created. Has no effect if the directory structure already exists.
    :param eager_logging: If true, the logged metrics and hyperparams will be saved to file immediately.
            If false, the logger will wait until save() is called, and until then, will hold metrics and hyperparams
            in memory. Watch out not to run out of memory!
    """

    logger = DAGsHubLogger(
        metrics_path=metrics_path,
        should_log_metrics=should_log_metrics,
        hparams_path=hparams_path,
        should_log_hparams=should_log_hparams,
        should_make_dirs=should_make_dirs,
        eager_logging=eager_logging,
    )
    try:
        yield logger
    finally:
        logger.save()
        logger.close()
