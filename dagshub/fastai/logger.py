from fastai.callback.core import Callback
from fastai.torch_core import rank_distrib, to_detach

from ..logger import DAGsHubLogger as LoggerImpl


class DAGsHubLogger(Callback):
    """
    First, install the DAGsHub logger with
    `pip install dagshub`

    Example of Usage:
    ```
    from dagshub.fastai import DAGsHubLogger

    # To log only during a single training phase
    learn.fit(..., cbs=DAGsHubLogger())
    ```
    """

    def __init__(self,
                 metrics_path: str = 'metrics.csv',
                 should_log_metrics: bool = True,
                 hparams_path: str = 'params.yml',
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
        self.logger = LoggerImpl(metrics_path=metrics_path, should_log_metrics=should_log_metrics,
                                 hparams_path=hparams_path, should_log_hparams=should_log_hparams,
                                 should_make_dirs=should_make_dirs, eager_logging=False)
        self._dags_status_hyperparam_name = 'success'
        self._dags_step_num = -1
        self._dags_epoch = 0

    def before_fit(self):
        # Make sure this is a training run
        self.run = not hasattr(self.learn, 'lr_finder') and \
                   not hasattr(self, "gather_preds") and rank_distrib() == 0
        if not self.run:
            return

        # Log Hyper Parameters
        params = self.learn.gather_args()
        self.logger.log_hyperparams(params)

    def after_batch(self):
        if self.learn.training:
            self._dags_step_num += 1
            hypers = {f'{k}_{i}': v for i, h in enumerate(self.opt.hypers) for k, v in h.items()}
            metrics = {
                'train_loss': to_detach(self.learn.smooth_loss.clone()).numpy(),
                'raw_loss': to_detach(self.learn.loss.clone()).numpy(),
                **hypers
            }
            self.logger.log_metrics(metrics, step_num=self._dags_step_num)

    def after_epoch(self):
        self._dags_epoch += 1
        metrics = {n: s for n, s in zip(self.recorder.metric_names, self.recorder.log) if n not
                   in ['train_loss', 'epoch', 'time']}
        metrics['epoch'] = self._dags_epoch
        self.logger.log_metrics(metrics, step_num=self._dags_step_num)

    def after_fit(self):
        self.run = True
        if self._dags_status_hyperparam_name is not None and \
                self._dags_status_hyperparam_name not in self.logger.hparams:
            self.logger.log_hyperparams({self._dags_status_hyperparam_name: self.run})
        try:
            self.logger.save()
            self.logger.close()
        except:
            print('Fitting model has already been ended')
