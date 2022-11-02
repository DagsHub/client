[![DagsHub Client](dagshub_github.png)](https://dagshub.com)

<div align="center">
    <h3>🚀 Launching <a href="#data-streaming">Streaming</a> and <a href="#data-streaming">Upload</a> of DVC versioned Data 🚀</h3>
</div>
<br/>

[![Tests](https://github.com/dagshub/client/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/DAGsHub/client/actions/workflows/python-package.yml)
[![pip](https://img.shields.io/pypi/v/dagshub.svg?label=pip&logo=PyPI&logoColor=white)](https://pypi.org/project/dagshub)
[![License](https://img.shields.io/pypi/l/dagshub)](/LICENSE)

[![DagsHub Sign Up](https://img.shields.io/badge/DagsHub-Sign%20Up-%231F4C55?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAACXBIWXMAAACXAAAAlwHUBiyCAAACmUlEQVRIieVXsYoUQRB9nouY7QQGBoITGumYiCDimBiYuKZnMibG+wfOJ6z+wE2kmbbBgSa6CwoqCHtofnuIoTCbiUlJ6euz7O3p23U9LvBBM71d3fVqqqqrZo+JCI4CG0fCCqDHZwZgyPmY41CxYciUvAXgAIwOgXRAnp+6lTgnqSNxzuGN+ReoSPiIBhQQkVJExiJSyy9MRaQQkUZEZiJSiUimSfgXQ8+NqPOOiLTkKr2wJYFFRaMayusViD1hy/NXOW9pRN6je9Wt5wKXbgG4SzflDIWiBlBG3O8TMuN8ynMt530AEwDXAMx8VjckCLFl5BqbXQD3qWBGpRkJChJkfHp9augFzr/wLKxrvBtiKLhvEMTbmb0au3t0sZcXga6HXm7josTbHcRNRyzrYF8oD19km8b/Ubk0hvOIuyemuKSwE5HZevAJwE2fC5a4oeCNWZsztu0SxLE9qvMB5+8APPP7LPGYG/u0DkyQZUhT0OT6DOCG9UDYJNSlHwAcB/DYXKF1oIY/AfDS9oBYd1Ky9wA2I7L8gN9dcOHZGHHBOxpbnzIcdi00KrzHiIVrlX5cMf4D00h07HH4hlKyYNibsEDcCxcS8IoaEtY0pG+OOK7fDnr6QkhWIQZdOGK99djhG6nbb3FMTA+A6cW/Eak2VaRSlWyRqYqWR+RaRs+zKuZWZ4w4J4kl7YIqHLImu449H0VkTj1JYpC4NPN14Tj2ObqyesQk0bidPSDurzhSyBc+oxJfEWNa2Sbe9rmZP03sdWHepD7oM1O7FRc518bxFsAJANeDM68BfAVwCsAVZvd3AJfCzE5dp5abh6Z4gM/TdN8LAN+4fhLAZSo/w7WCv0texX2s8xcmM1UMLLNu2W72n/13AvADffO77cDRF5EAAAAASUVORK5CYII=)](https://dagshub.com/user/sign_up?redirect_to=)
[![Discord](https://img.shields.io/discord/698874030052212737?logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAAB4AAAAXCAYAAAAcP%2F9qAAAACXBIWXMAAAsTAAALEwEAmpwYAAAFN2lUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNi4wLWMwMDMgNzkuMTY0NTI3LCAyMDIwLzEwLzE1LTE3OjQ4OjMyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iIHhtbG5zOnBob3Rvc2hvcD0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3Nob3AvMS4wLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiIHRpZmY6T3JpZW50YXRpb249IjEiIHhtcDpDcmVhdGVEYXRlPSIyMDIxLTEwLTIzVDE2OjI5OjAyKzAzOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0xMC0yM1QxNjozNDoxMiswMzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0xMC0yM1QxNjozNDoxMiswMzowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpiMTBhMTRjOC1iNzg5LTQ2OTgtYmVhMi1kZTI4NDg3ZmEyMjIiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6YjEwYTE0YzgtYjc4OS00Njk4LWJlYTItZGUyODQ4N2ZhMjIyIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6YjEwYTE0YzgtYjc4OS00Njk4LWJlYTItZGUyODQ4N2ZhMjIyIj4gPHhtcE1NOkhpc3Rvcnk%2BIDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6YjEwYTE0YzgtYjc4OS00Njk4LWJlYTItZGUyODQ4N2ZhMjIyIiBzdEV2dDp3aGVuPSIyMDIxLTEwLTIzVDE2OjM0OjEyKzAzOjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgMjIuMSAoTWFjaW50b3NoKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE%2BIDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24%2BIDwvcmRmOlJERj4gPC94OnhtcG1ldGE%2BIDw%2FeHBhY2tldCBlbmQ9InIiPz4jeahYAAACnElEQVRIx62WPWxOURjH7%2Fu%2BrTdN1RsGIkgw2BBLQwxCmvgamzAxCAs2xCYGSZWBWYihSUcDFhJpJJ1M0kUqJS1BlRCk%2Bno%2F7s%2FyPPV38lwtcZKTc%2B89z33%2B%2F%2BfznAzIkllO3lcD%2FcAloBbI%2B9wMDAB7ArlSKl8EWgWOAA%2BAWX6Ni8AaoA84AOwDdhm5%2ByL3ARgG9haBK2jF1rXAJL%2BPps2ikdvaANrJ3sMIXIE7bL1jP3w3sDxRjilv2WwX7DeAur2fM92dKbCD7hbmRZbli%2Fjmo2XrF2ClhtPN99g%2BWgD4X8YPWwfUao3tDnFT%2Fh%2BBPRQfJdtL6vebCcM0uRoLEGrbv61gzz14wq32GPcA7xOGHr92Qdz%2B9K0VEMdCmQFlB96fCKRZOgIMAd8Cxf48CdwCxgID%2FHnWynU%2Bq68GSeUKz0rJbQTeiTInOqqlYiTVkFz09SvwSCLo65go67b1tJB0r2yXkGXAKusDaq0bddmBu4BXiZUuNCx1Xklq3cl9NSCtkArwrEDnPQdeF7BzpU%2Bk6N3i44HFWxOLVxihSOdTB95SkFDO9Ki4uwZMyL4ru5scNteDZHV9U0A1s%2FhErU%2Bfh%2BxYnAqyui3euWAnGkHNu9wMUNOOFfXcZtA%2BF1PH9aD%2BtYMtz4BeAckDQeS0qssR2RJ3N4E5yRUKTiyAaaAnAzbI5lzSrW6biz%2F%2FRW9%2BCZwBHgtg23QDPNc67pOSQs7RF8ApYBtwGLhhzWICeAu8AcatFV6zW0mvkf1kRtRF7yiwyYH9SOwCrhTcNA4mWdtppbNUatfnYBD3GeCkXrGy9GYArLdymE5KpWqNpBRc9ErAElu7gdf27zhw3gi6XEd69SknBJYBx4yIesYvDj5LQsat3wkcCrw0T%2FonycbE%2FgQEhDUAAAAASUVORK5CYII%3D)](https://discord.com/invite/9gU36Y6)
[![DagsHub on Twitter](https://img.shields.io/twitter/follow/TheRealDAGsHub.svg?style=social)](https://twitter.com/TheRealDAGsHub)

# What is DagsHub
**DagsHub** is a platform where machine learning and data science teams can build, manage, and collaborate on their projects.
With DagsHub you can:
1. **Version code, data, and models** in one place. Use the free provided DagsHub storage or connect it to your cloud storage
2. **Track Experiments** using Git, DVC or MLflow, to provide a fully reproducible environment
3. **Visualize** pipelines, data, and notebooks in and interactive, diff-able, and dynamic way
4. **Label** your data directly on the platform using Label Studio
5. **Share** your work with your team members
6. **Stream and upload** your data in an intuitive and easy way, while preserving versioning and structure.

DagsHub is built firmly around open, standard formats for your project. In particular:
* Git
* [DVC](https://github.com/iterative/dvc)
* [MLflow](https://github.com/mlflow/mlflow)
* [Label Studio](https://github.com/heartexlabs/label-studio)
* Standard data formats like YAML, JSON, CSV

Therefore, you can work with DagsHub regardless of your chosen programming language or frameworks.

# DagsHub Client API & CLI

__This client library is meant to help you get started quickly with DagsHub__. It is made up of Experiment tracking and
Direct Data Access (DDA), a component to let you stream and upload your data.

This Readme is divided into segments based on functionality:
1. [Installation & Setup](#installation-and-setup)
2. [Data Streaming](#data-streaming)
3. [Data Upload](#data-upload)
4. [Experiment Tracking](#experiment-tracking-logger)

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
All the supported ways to use DDA should normally automatically detect the configuration needed, including:
* The Git/DVC project in the current working directory
* The DagsHub repository URL to stream files from
* The Username and Token to use for streaming files from DagsHub

If you need to override the automatically detected configuration, use the following environment variables and options in
the CLI:

* `--repo` (a command line option)
* `DAGSHUB_USERNAME`
* `DAGSHUB_PASSWORD`
* `DAGSHUB_USER_TOKEN`

Or provide the relevant arguments to the Python entrypoints:

* `repo_url=`
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
2. [Mounted Filesystem - Experimental](#mounted-filesystem)
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
dagshub upload <repo_owner>/<repo_name> <local_file_path> <path_in_remote>
```

**Options**
```bash
-m, --message TEXT  Commit message for the upload
-b, --branch TEXT   Branch to upload the file to - this is required for private repositories
--update            Force update an existing file
-v, --verbose       Verbosity level
--help              Show this message and exit.
```

> **Note** **Important**
> For uploading to private repositories, you must use the `--branch BRANCH_NAME` option.

### Python API Upload

You can use the DagsHub client to upload files directly from your Python code to your DagsHub repo, **using both Git &
DVC.**

#### Usage
Basic usage example is as follows:

```python
from dagshub.upload import Repo

repo = Repo("<repo_owner>", "<repo_name>")  # Optional: username, password, token, branch

# Upload a single file to a repository in one line
repo.upload(file="<local_file_path>", path="<path_in_remote>", versioning=”dvc”)  # Optional: versioning, new_branch, commit_message
```

This will upload a single file to DagsHub, which will be tracked by DVC.

> **Note** **Important**
> For uploading to private repositories, you must use the `branch=BRANCH_NAME` option.

You can also upload multiple files with the Python client, by using:
```python
# Upload multiple files to a dvc folder in a repository with a single commit
ds = repo.directory("<name_of_remote_folder")

# Add file-like object
f = open("<local_file_path>", 'rb')
ds.add(file=f, path="<path_in_remote>")

# Or add a local file path
ds.add(file="<local_file_path>", path="<path_in_remote>")
ds.commit("<commit_message>", versioning="dvc")
```

This will upload a folder with multiple files simultaneously, with a custom commit message to your DagsHub repo.

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

---

Made with 🐶 by [DagsHub](https://dagshub.com/).
