# [pytorch-lightning](https://github.com/williamFalcon/pytorch-lightning/) [DAGsHub](https://dagshub.com) integration

This package allows you to output logs from `pytorch-lightning` runs to a simple, open format used by DAGsHub.

These logs include your metrics and hyperparameters, essential information to keep a record of your experiments.

## Usage
```bash
pip install pytorch-lightning-dagshub
```
```python
from pytorch-lightning-dagshub import DAGsHubLogger
from pytorch_lightning import Trainer

trainer = Trainer(
    logger=DAGsHubLogger(),
    default_save_path='lightning_logs',
)
```

By default, `DAGsHubLogger` will save the following two files:
* `lightning_logs/metrics.csv` - A CSV file containing all the run's metrics.
* `lightning_logs/params.yml` - A YAML file containing all the run's hyperparameters, plus an additional "status" field to
indicate whether the run was successful.
