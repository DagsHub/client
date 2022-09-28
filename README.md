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


# Data Streaming

By using the DagsHub client, you can stream files from your DagsHub repository without needing to download them to your local disk ahead of time! You'll no longer need to wait for the lengthy `dvc pull` to complete before you start training your models, you can launch the script immediately after connecting DagsHub Streaming and watch as the data files automatically get downloaded as they are needed!

The DagsHub client is designed specifically to make streamed files nearly *indistinguishable* from real files saved to your disk!  
Using any of the supported integration methods, streamed files will appear alongside real files, and when your code attempts to read from them, they will transparently first be converted into real files and cached on disk for future uses.

Supported ways to enable the DagsHub Streaming include:

## 1. Python-only "Lite" Hooks
This method automatically detects calls to Python's built-in file operations (such as `open()`), and if the files exist on your DagsHub repo, will load them on the fly as they're requested.
This means that most Python ML and data libraries will automatically work with this method, without requiring any manual integration!
```python
from dagshub.streaming import install_hooks
install_hooks()
```
Note that some popular ML frameworks, such as TensorFlow, have input/output routines written in C/C++, so they will not see the new files.
For those frameworks, check out the alternative methods below.

## 2. CLI launcher
Launch a terminal, and `cd` into the directory of your project. Then run
```bash
$ dagshub-mount
```
If you launch a new terminal and navigate to that directory, or run `cd .` in any existing terminals in that directory, you should now be able to see that any files in your repository but not saved locally appear in your directory listings! Run
```bash
$ cat .dagshub-streaming
```
from the root of your project to confirm that the streaming works.

This works by mounting a FUSE filesystem, and therefore is only supported on Linux, or on Mac and Windows with custom setup.
It also means that any non-Python programs you want to run on your data will work without any added integration effort!

## 3. Python entrypoint
This method is the same as the CLI launcher, and also mounts a FUSE filesystem, except you can execute it from inside your Python code.

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


## 4. No-magic Python API
If you hate magic and want to explicitly and unambigiously state that you're using DagsHub Streaming, or else none of the other methods are supported on your machine, we also offer a straightforward Python client class that you can use:
```python
from dagshub.streaming import DagsHubFilesystem
fs = DagsHubFilesystem()
```
Then replace any use of `open()`, `os.stat()`, `os.listdir()`, and `os.scandir()` with `fs.open()`, `fs.stat()`, `fs.listdir()`, and `fs.scandir()` respectively.  
You don't even have to provide relative paths from the project directory, we take care of that for you!  
Pass the exact same arguments you would to the built-in functions to our client's functions, and streaming functionality will be provided.  
e.g.:  `fs.open('/full/path/from/root/to/dvc/managed/file')`

## Automagic Configuration
All of the supported ways to enable DagsHub Streaming should automatically detect the configuration needed, including
- the git/dvc project folder on disk
- the DagsHub repository URL to stream files from
- the username and token to stream files from DagsHub

If you need to override the automatically detected configuration, pass the `--repo_url`, `--username`, and `--password` flags to the CLI, or the `repo_url=`, `username=`, and `password=` keyword arguments to either of the python entrypoints.

# Data Upload
*You don't need to pull the entire dataset anymore.*

The upload API lets you append files to existing DVC directories, without downloading anything to your maching, quickly and efficiently.

You can use the DagsHub client to upload files directly to DagsHub, **using both Git & DVC.**
A basic use looks like this:
```python
from dagshub.upload import Repo

repo = Repo("idonov8", "baby-yoda-segmentation-dataset", branch="new_annotations")
ds = repo.directory("images")

with open("test_photo.png", 'rb') as f:
    # 'target_dir' is just the enclosing directory name. 
    ds.add(file=f, target_dir="test_images") 
    ds.commit("Add a photo with the api using a file object", versioning="dvc")

# 'path' is a full path, including the file name.	
ds.add(file="test_photo.png", path="test_images/my_awesome_image.png")
ds.commit("Add a photo with the api using plain text", versioning="dvc")
```
# Training Logger
## Guide
You can learn more by completing our short [tutorial](https://dagshub.com/docs/experiment-tutorial/overview/) or reading the [docs](https://dagshub.com/docs)

## Alternative - use DagsHub's MLflow logging
The logging in this client library helps you create Git commits as experiments - if instead you prefer to log experiments on the fly with Python code, without committing every result to Git, then [check out our MLflow integration](https://dagshub.com/docs/integration_guide/mlflow_tracking/) instead.

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
* If you want support for another framework - [please open an issue](https://github.com/DagsHub/client/issues/new).

---

Made with 🐶 by [DagsHub](https://dagshub.com/).
