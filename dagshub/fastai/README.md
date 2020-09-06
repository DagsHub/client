# [Fastai v2](https://github.com/fastai/fastai) + [DAGsHub](https://dagshub.com) integration

This package allows you to output logs from `fastai` runs to a simple, open format used by DAGsHub.

These logs include your metrics and hyperparameters, essential information to keep a record of your experiments.

## Usage
```bash
pip install dagshub
```
```python
from dagshub.fastai import DAGsHubLogger

# To log only during a single training phase
learn.fit(..., cbs=DAGsHubLogger())
```

By default, `DAGsHubLogger` will save the following two files:
* `metrics.csv` - A CSV file containing all the run's metrics.
* `params.yml` - A YAML file containing all the run's hyperparameters, plus an additional "status" field to
    indicate whether the run was successful.

---

Made with 🐶 by [DAGsHub](https://dagshub.com/).
