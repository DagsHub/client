<div align="center">
  <a href="https://dagshub.com"><img src="https://raw.githubusercontent.com/DAGsHub/client/master/dagshub_github.png" width=600 alt=""/></a><br><br>
</div>

[![Build Status](https://travis-ci.org/DAGsHub/client.svg?branch=master)](https://travis-ci.org/DAGsHub/client)
[![pypi](https://img.shields.io/pypi/v/dagshub.svg)](https://pypi.python.org/pypi/dagshub)


# DAGsHub Python client libraries
Use DAGsHub to create reproducible versions of your data science research project, 
allow others to understand your project, and to contribute back to it.

DAGsHub is built firmly around open, standard formats for your project. In particular:
* git
* [DVC](https://github.com/iterative/dvc)
* Standard data formats like YAML, JSON, CSV

Therefore, you can work with DAGsHub regardless of your chosen programming language or frameworks. 

__This client library is meant to help you get started quickly in Python__, but it's purely optional - 
the data formats are very simple and you can choose to work with them directly. 

You can learn more by completing our short [tutorial](https://dagshub.com/docs/overview) or reading the [docs](https://dagshub.com/docs)

## Installation
```bash
pip install dagshub
```

## Basic Usage
```python
from dagshub import dagshub_logger, DAGsHubLogger

# As a context manager:
with dagshub_logger() as logger:
    # Metrics:
    logger.log_metrics(loss=3.14, step_num=1)
    # OR:
    logger.log_metrics({'val_loss': 6.28}, step_num=2)
    
    # Hyperparameters:
    logger.log_hyperparams(lr=1e-4)
    # OR:
    logger.log_hyperparams({'optimizer': 'sgd'})
    

# As a normal Python object:
logger = DAGsHubLogger()
logger.log_hyperparams(num_layers=32)
logger.log_metrics(batches_per_second=100, step_num=42)
# ...
logger.save()
logger.close()
```

## Integrations with ML frameworks
The [basic DAGsHub logger](dagshub/logger.py) is just plain Python, and requires no specific framework.

However, for convenience, we include some integrations with common ML frameworks, which can __just work__ right out of the box, 
without having to write any logging code on your own:

* [pytorch-lightning](dagshub/pytorch_lightning)
* More - soon to come!


---

Made with 🐶 by [DAGsHub](https://dagshub.com/).
