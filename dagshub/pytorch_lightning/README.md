# [pytorch-lightning](https://github.com/williamFalcon/pytorch-lightning/) + [DAGsHub](https://dagshub.com) integration

This package allows you to output logs from `pytorch-lightning` runs to a simple, open format used by DAGsHub.

These logs include your metrics and hyperparameters, essential information to keep a record of your experiments.

## Usage
```bash
pip install dagshub
```
```python
from dagshub.pytorch_lightning import DAGsHubLogger
from pytorch_lightning import Trainer

trainer = Trainer(
    logger=DAGsHubLogger()
)
```

By default, `DAGsHubLogger` will save the following two files:
* `lightning_logs/metrics.csv` - A CSV file containing all the run's metrics.
* `lightning_logs/params.yml` - A YAML file containing all the run's hyperparameters, plus an additional "status" field to
    indicate whether the run was successful.

## Examples

See examples in:
* [examples/hyperparams-as-dependency](/examples/pytorch-lightning/hyperparams-as-dependency/) <br/>
    Gives a framework for setting up your hyperparameter file as a [DVC](https://dvc.org) __dependency__ of the training stage. <br/>
    This means that you manually edit your [params.yml file](../../examples/pytorch-lightning/hyperparams-as-dependency/params.yml) before training,
    then use [`dvc repro`](https://dvc.org/doc/command-reference/repro) to run the training stage.
    In theory, this is the correct workflow with DVC.
    
* [examples/hyperparams-as-output](/examples/pytorch-lightning/hyperparams-as-output/) <br/>
    Gives a framework for setting up your hyperparameter file as a [DVC](https://dvc.org) __output__ of the training stage. <br/>
    This means that you can keep using `pytorch-lightning` from the command line as usual, specifying hyperparameters as
    command arguments. <br/>
    After training is done and you're happy with the results, you can set the results in stone and make them reproducible
    using [`dvc commit`](https://dvc.org/doc/command-reference/commit).

---

Made with 🐶 by [DAGsHub](https://dagshub.com/).
