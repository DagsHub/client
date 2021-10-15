# [Keras](https://github.com/keras-team/keras/) + [DAGsHub](https://dagshub.com) integration

This package allows you to output logs from `tensorflow.keras` runs to a simple, open format used by DAGsHub.

These logs include your metrics and hyperparameters, essential information to keep a record of your experiments.

## Usage
```bash
pip install dagshub
```
```python
from dagshub.keras import DAGsHubLogger

model = ...

model.fit(
    dataset,
    ...,
    callbacks=[DAGsHubLogger()]
)
```

By default, `DAGsHubLogger` will save the following two files:
* `metrics.csv` - A CSV file containing all the run's metrics.
* `params.yml` - A YAML file containing all the run's hyperparameters, plus an additional "status" field to
    indicate whether the run was successful.

## Examples

- [examples/keras/mnist.py](https://github.com/dagshub/client/blob/master/examples/keras/mnist.py)

  Basic smoke-test to demonstrate that the `DAGsHubLogger` callback works and is usable from a run-of-the-mill Keras model.

---

Made with 🐶 by [Arjun Vikram](https://github.com/arjvik) and [DAGsHub](https://dagshub.com/).

