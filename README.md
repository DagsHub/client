<div align="center">
  <a href="https://dagshub.com"><img src="dagshub_github.png" width=600 alt=""/></a><br><br>
</div>

[![Discord](https://img.shields.io/discord/698874030052212737)](https://discord.com/invite/9gU36Y6)
[![Tests](https://github.com/dagshub/client/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/DAGsHub/client/actions/workflows/python-package.yml)
[![pypi](https://img.shields.io/pypi/v/dagshub.svg)](https://pypi.python.org/pypi/dagshub)
[![Updates](https://pyup.io/repos/github/DAGsHub/client/shield.svg)](https://pyup.io/repos/github/DAGsHub/client/)
[![License](https://img.shields.io/pypi/l/dagshub)](/LICENSE)
<a href="https://twitter.com/TheRealDAGsHub" title="DagsHub on Twitter"><img src="https://img.shields.io/twitter/follow/TheRealDAGsHub.svg?style=social"></a>

# DagsHub Python client libraries
Use DagsHub to create reproducible versions of your data science research project, 
allow others to understand your project, and to contribute back to it.

DagsHub is built firmly around open, standard formats for your project. In particular:
* git
* [DVC](https://github.com/iterative/dvc)
* Standard data formats like YAML, JSON, CSV

Therefore, you can work with DagsHub regardless of your chosen programming language or frameworks. 

__This client library is meant to help you get started quickly in Python__, but it's purely optional - 
the data formats are very simple and you can choose to work with them directly. 



## Installation
```bash
pip install dagshub
```

# Training Logger
## Guide
You can learn more by completing our short [tutorial](https://dagshub.com/docs/experiment-tutorial/overview/) or reading the [docs](https://dagshub.com/docs)

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
The [basic DagsHub logger](https://github.com/DAGsHub/client/blob/master/dagshub/logger.py) is just plain Python, and requires no specific framework.

However, for convenience, we include some integrations with common ML frameworks, which can __just work__ right out of the box, 
without having to write any logging code on your own:

* [pytorch-lightning](https://github.com/DAGsHub/client/tree/master/dagshub/pytorch_lightning) – supports version 1.4.0 or higher
* [fastai v2](https://github.com/DAGsHub/client/tree/master/dagshub/fastai)
* [keras](https://github.com/DAGsHub/client/tree/master/dagshub/keras)
* More - soon to come!

# Data Streaming

By using the DagsHub client, you can stream files from your DagsHub repository without needing to download them to your local disk ahead of time! You'll no longer need to wait for the lengthy `dvc pull` to complete before you start training your models, you can launch the script immediately after connecting DagsHub Streaming and watch as the data files automatically get downloaded as they are needed!

The DagsHub client is architectured specifically to make streamed files nearly *indistinguishable* from real files saved to your disk! Using any of the supported integration methods, streamed files will appear alongside real files, and when your code attempts to read from them, they will transparently first be converted into real files and cached on disk for future uses!

Supported ways to enable the DagsHub Streaming include

## 1. CLI launcher
Launch a terminal, and `cd` into the directory of your project. Then run
```bash
$ dagshub-mount
```
If you launch a new terminal and navigate to that directory, or run `cd .` in any existing terminals in that directory, you should now be able to see that any files in your repository but not saved locally appear in your directory listings! Run
```bash
$ cat .dagshub-streaming
```
from the root of your project to confirm that the streaming works.

## 2. Python entrypoint
Simply add
```python
from dagshub.streaming import mount
mount()
```
to your Python program, and any files in your repository but not saved locally will appear in your directory listings! Run
```python
print(open(PROJECT_ROOT_DIRECTORY + '/.dagshub-streaming').read())
```
to confirm that the streaming works.

## 3. Python-only "Lite" Hooks
If hooking into the operating system's filesystem layer is too hard-core for you, we also provide a way to only hook into Python's filesystem operations. Run
```python
from dagshub.streaming import install_hooks
install_hooks()
```
Note that many popular ML frameworks such as PyTorch and TensorFlow have input/output routines written in C/C++, so they will not see the new files.

## 4. No-magic Python API
If you hate magic and want to explicitly and unambigiously state that you're using DagsHub Streaming, we also offer a boring Python client class that you can use
```python
from dagshub.streaming import DagsHubFilesystem
fs = DagsHubFilesystem()
```
Then replace any use of `open()`, `os.stat()`, `os.listdir()`, and `os.scandir()` with `fs.open()`, `fs.stat()`, `fs.listdir()`, and `fs.scandir()` respectively. You don't even have to provide relative paths from the project directory, we take care of that for you! Pass the exact same arguments you would to the built-in functions to our client's functions, and streaming functionality will be provided.

## Automagic Configuration
All of the supported ways to enable DagsHub Streaming should automatically detect the configuration needed, including
- the git/dvc project folder on disk
- the DagsHub repository URL to stream files from
- the username and token to stream files from DagsHub

If you need to override the automatically detected configuration, pass the `--repo_url`, `--username`, and `--password` flags to the CLI, or the `repo_url=`, `username=`, and `password=` keyword arguments to either of the python entrypoints.

---

Made with 🐶 by [DagsHub](https://dagshub.com/).
