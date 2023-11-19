# DagsHub Client Docs

__This client library is meant to help you get started quickly with DagsHub__. It is made up of Experiment tracking and
Direct Data Access (DDA), a component to let you stream and upload your data.

This Readme is divided into segments based on functionality:
1. [Installation & Setup](#installation-and-setup)
2. [Data Engine](data_engine.md)
3. [Data Streaming](#data-streaming)
4. [Data Upload](#data-upload)
5. [Experiment Tracking](#experiment-tracking-logger)
   1. [Autologging](#autologging-integrations-with-ml-frameworks)

Some functionality is supported only in Python.

To read about some of the awesome use cases for Direct Data Access, check out
the [relevant doc page](https://dagshub.com/docs/feature_guide/direct_data_access/#use-cases).

## Installation and Setup
```bash
pip install dagshub
```

Direct Data Access (DDA) functionality requires authentication, which you can easily do by running the following command
in your terminal:
```bash
dagshub login
```

This process will generate and cache a short-lived token in your local machine, and allow you to perform actions that
require authentication. After running `dagshub login` you can use data streaming and upload files without providing
authentication info. You can also provide a non-temporary token by using the `--token` flag.

### Automagic Configuration
Parts of DDA will try to pick up configuration required to communicate with DagsHub. For example, Data Streaming will use the configuration of your git repository to get the branch you're currently working on and your authentication username and password.

OAuth token acquired via `dagshub login` is cached locally, so you don't need to log in every time you run your scripts.

If you need to override the automatically detected configuration, use the following environment variables and options in
the CLI:

* `--repo` (a command line option)
* `DAGSHUB_USERNAME`
* `DAGSHUB_PASSWORD`
* `DAGSHUB_USER_TOKEN`

Or provide the relevant arguments to the Python entrypoints:

* `repo_url=` (For Data Streaming)
* `username=`
* `password=`
* `token=`

## Data Streaming
By using the DagsHub client, you can stream files from your DagsHub repository without needing to download them to your
local disk ahead of time! You'll no longer need to wait for the lengthy `dvc pull` to complete before you start training
your models, you can launch the script immediately after connecting DagsHub Streaming and watch as the data files
automatically get downloaded as they are needed!

The DagsHub client is designed specifically to make streamed files nearly *indistinguishable* from real files saved to
your disk! Using any of the supported integration methods, streamed files will appear alongside real files, and when
your code attempts to read from them, they will transparently first be converted into real files and cached on disk for
future uses.

Supported ways to enable the DagsHub Streaming include:
1. [Magical Python Hooks](#python-hooks)
2. [Mounted Filesystem - Experimental](#mounted-filesystem---experimental)
3. [Non-magical API](#non-magical-api)

### Python Hooks
**We recommend using Python Hooks over the Mounted Filesystem which is currently experimental**

The Python Hooks method automatically detects calls to Python's built-in file operations (such as `open()`), and if the
files exist on your DagsHub repo, it will load them on the fly as they're requested. This means that most Python ML and
data libraries will automatically work with this method, without requiring manual integration.

#### Usage
To use Python Hooks, open your DagsHub project, and copy the following 2 lines of code into your Python code which accesses your data:
```python
from dagshub.streaming import install_hooks
install_hooks()
```
That’s it! You now have streaming access to all your project files.

**Note:** You can stream files from a spesific branch or commit by setting the `branch` parameter.


To see an example of this that actually runs, check out the Colab below:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1CtBmcDtZnxZKVIhNvPagX-8UFWHZ5HAg?usp=sharing)

> **Note** **Known Limitations**
> 1. Some frameworks, such as TensorFlow and OpenCV, which rely on routines written in C or C++ for file input/output, are currently not supported.
> 2. `dvc repro` and `dvc run` commands for stages that have dvc tracked files in deps will not work, showing errors of missing data, to run a stage, use the `--downstream` flag instead, or run it manually, and use `dvc commit`.

### Mounted Filesystem - Experimental
The Mounted Filesystem approach uses FUSE under the hood. This bypasses the limitations in the Python Hooks approach by
creating a fully virtual filesystem that connects your remote to the local workspace. It supports all frameworks and
non-Python languages. However, note that FUSE only supports Linux machines and is currently unstable.

#### Usage
To use the Mounted Filesystem, simply clone your DagsHub repository, then run the following command in your terminal:
```bash
dagshub mount
```

You should see all your remote files magically appear, you'll be able to open them via the file explorer and your code.

### Non-magical API
Magic is awesome, but sometimes you need more control over how you access your project files and prefer a direct API. If
you want to explicitly and unambiguously state that you're using DagsHub Streaming, or else none of the other methods
are supported on your machine, we also offer a straightforward Python client class that you can use.

#### Usage
Just copy the following code into your Python code:
```python
from dagshub.streaming import DagsHubFilesystem
fs = DagsHubFilesystem()
```

Then replace any use of Python file-handling function in the following way:

* `open()` → `fs.open()`
* `os.stat()` → `fs.stat()`
* `os.listdir()` → `fs.listdir()`
* `os.scandir()` → `fs.scandir()`

You can pass the same arguments you would to the built-in functions to our client's functions, and streaming
functionality will be provided. e.g.:
```python
fs.open('/full/path/from/root/to/dvc/managed/file')
```

## Data Upload
*You don't need to pull the entire dataset anymore.*

The upload API lets you upload or append files to existing DVC directories, without downloading anything to your
machine, quickly and efficiently. This utility is especially useful for active learning scenarios, when you want to
append a new file to your dataset.

With the client, you can upload files in 2 main ways:
1. [CLI Upload](#cli-upload)
2. [Python API Upload](#python-api-upload)

### CLI Upload

Upload a single file to any location in your repository, including DVC directories.

#### Usage
```bash
dagshub upload <repo_owner>/<repo_name> <local_file_path> [<path_in_remote> (optional)]
```

**Options**
```bash
-m, --message TEXT  Commit message for the upload
-b, --branch TEXT   Branch to upload the file to - this is required for private repositories
--update            Force update an existing file
-v, --verbose       Verbosity level
--help              Show this message and exit.
```

### Python API Upload

You can use the DagsHub client to upload files directly from your Python code to your DagsHub repo, **using both Git &
DVC.**

#### Usage
Basic usage example is as follows:

```python
from dagshub import upload_files

upload_files("<repo_owner>/<repo_name>", local_path="<path_to_file_or_dir_to_upload>")
# Optional: remote_path, commit_message, username, password, token, branch, commit_message, versioning
# For a full list of potential options, see dagshub.upload.wrapper.Repo.upload_files
```

This will upload a single file or directory to DagsHub, which will be tracked by DVC.

You can also customize this behavior, and upload multiple files programmatically with the Python client, by using:

```python
from dagshub.upload import Repo
repo = Repo("<repo_owner", "<repo_name>")

# Upload multiple files to a dvc folder in a repository with a single commit
ds = repo.directory("<name_of_remote_folder")

# Add file-like object
f = open("<local_file_path>", 'rb')
ds.add(file=f, path="<path_in_remote>")

# Or add a local file path
ds.add(file="<local_file_path>", path="<path_in_remote>")
ds.commit("<commit_message>", versioning="dvc")
```

## Experiment Tracking Logger

DagsHub helps you track experiment and make your work reproducible using Git and/or MLflow.

### Git Tracking
Git is used in most data science projects and let's, which lets us track, version, and reproduce code files easily.
Therefore, DagsHub supports Git and expands its capabilities to track experiments as well. Using Git to track the
experiment, we can also encapsulate the code, data, and model that produced a certain result. This way, even when the
project evolves or grows in complexity, we can easily reproduce experimental results.

#### Usage
You can learn more by completing our short [tutorial](https://dagshub.com/docs/getting_started/overview/), or reading
the [experiment tracking docs](https://dagshub.com/docs/feature_guide/git_tracking/)

Below is a basic usage example:
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

#### Autologging integrations with ML frameworks
The [basic DagsHub logger](https://github.com/DagsHub/client/blob/master/dagshub/logger.py) is just plain Python, and requires no specific framework.

However, for convenience, we include some integrations with common ML frameworks, which can __just work__ right out of the box,
without having to write any logging code on your own:

* [pytorch-lightning](https://github.com/DagsHub/client/tree/master/dagshub/pytorch_lightning) – supports version 1.4.0 or higher
* [fastai v2](https://github.com/DagsHub/client/tree/master/dagshub/fastai)
* [keras](https://github.com/DagsHub/client/tree/master/dagshub/keras)
* If you want support for another framework - [please open an issue](https://github.com/DagsHub/client/issues/new).

### MLflow Tracking on DagsHub
The logging in this client library helps you create Git commits as experiments - if instead you prefer to log
experiments on the fly with Python code, without committing every result to Git,
then [check out our MLflow integration](https://dagshub.com/docs/integration_guide/mlflow_tracking/) instead.

## Help & Troubleshooting
### CLI Help
If you're not sure how to use any CLI commands, you can run:
```bash
dagshub <subcommand> --help
```
for any subcommand to get a usage description and list all the available options.
