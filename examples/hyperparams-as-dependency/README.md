# Hyperparameters as DVC dependency

This example how to set up your hyperparameter file as a [DVC](https://dvc.org) __dependency__ of the training stage. <br/>
This means that you manually edit your [params.yml file](params.yml) before training,
then use [`dvc repro`](https://dvc.org/doc/command-reference/repro) to run the training stage.
In theory, this is the correct workflow with DVC.

The relevant files are:
* [mnist_trainer.py](mnist_trainer.py) - the main script, defines the `pytorch-lightning` Trainer and connects it to the
    [DAGsHubLogger](../../pytorch_lightning_dagshub/logger.py).
* [params.yml](params.yml) - Hyperparameters to be used for the training run.
    To try an experiment with a different hyperparameter configurations, you should edit this file before running `dvc repro`. <br/>
    This YAML format is supported by DAGsHub, for smart experiment comparison and display.
* [metrics.csv](metrics.csv) - Output metrics from the training stage. <br/>
    This CSV format is supported by DAGsHub, for smart experiment comparison and display.   
* [train.dvc](train.dvc) - The DVC stage file.    

---

Made with 🐶 by [<img src="https://dagshub.com/img/favicon.svg" width=30 alt=""/>DAGsHub](https://dagshub.com/).
