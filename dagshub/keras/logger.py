from tensorflow.keras.callbacks import Callback

from ..logger import DAGsHubLogger as LoggerImpl


class ignore_exceptions:
    # Taken from fastcore code
    """Context manager to ignore exceptions"""

    def __enter__(self):
        pass

    def __exit__(self, *args):
        return True


class DAGsHubLogger(Callback):
    """
    First, install the DAGsHub logger with
    `pip install dagshub`

    Example of Usage:
    ```
    from dagshub.keras import DAGsHubLogger
    from tensorflow.keras import Trainer

    model = ...

    model.fit(
        dataset,
        ...,
        callbacks=[DAGsHubLogger()]
    )
    ```
    """

    def __init__(
        self,
        metrics_path: str = "metrics.csv",
        should_log_metrics: bool = True,
        hparams_path: str = "params.yml",
        should_log_hparams: bool = True,
        should_make_dirs: bool = True,
    ):
        """
        :param metrics_path (str): Where to save the single metrics CSV file.
        :param should_log_metrics (bool): Whether to log metrics at all. Should probably always be True.
        :param hparams_path (str): Where to save the single hyperparameter YAML file.
        :param should_log_hparams (bool): Whether to log hyperparameters to a file.
            Should be False if you want to work with hyperparameters in a dependency file,
            rather than specifying them using command line arguments.
        :param should_make_dirs (bool): If true, the directory structure required by metrics_path
            and hparams_path will be created. Has no effect if the directory structure already exists.
        """
        super(DAGsHubLogger, self).__init__()
        self.logger = LoggerImpl(
            metrics_path=metrics_path,
            should_log_metrics=should_log_metrics,
            hparams_path=hparams_path,
            should_log_hparams=should_log_hparams,
            should_make_dirs=should_make_dirs,
            eager_logging=True,
        )

    def on_train_begin(self, logs={}):
        params = {}
        with ignore_exceptions():
            params.update(self.params)
        with ignore_exceptions():
            params["optimizer"] = self.model.optimizer.get_config()
        with ignore_exceptions():
            params["loss"] = self.model.loss.get_config()
        self.logger.log_hyperparams(params)
        self.logger.log_hyperparams(success=False)
        self._epoch = -1
        self._step = 0

    def on_epoch_begin(self, epoch, logs={}):
        self._epoch = epoch

    def on_train_batch_end(self, batch, logs={}):
        self._step += 1
        self.on_epoch_end(None, logs)

    def on_epoch_end(self, epoch, logs={}):
        # At the end of an epoch, logs has more metrics
        metrics = {"epoch": self._epoch, **logs}
        self.logger.log_metrics(metrics, step_num=self._step)

    def on_train_end(self, logs={}):
        self.logger.log_hyperparams(success=True)
        self.logger.save()
        self.logger.close()
