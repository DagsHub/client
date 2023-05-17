# Data Engine (codename Data Shepherd) preliminary docs

## Warning: The interface for everything is still in development and is subject to big changes.

Let Kirill know if the README is not up to date and he will update

## Usage

Before using, make sure that your `DAGSHUB_CLIENT_HOST` env var is set to whatever host you connect to

**Make sure to import this before any dagshub import**

```python
import os
os.environ["DAGSHUB_CLIENT_HOST"] = "https://test.dagshub.com"
```

## Creating/Getting a datasource

### Creating

```python
from dagshub.data_engine.model import datasources

# Create a datasource
ds = datasources.create_from_bucket("simon/baby-yoda-segmentation-dataset", "bucket-ds", "s3://data-bucket/prefix")
```

If the datasource with name `bucket-ds` already exists, we will throw an error, so on further uses you need to get a
datasource

### Getting

```python
from dagshub.data_engine.model import datasources

# Can accept either name argument, or id argument
ds = datasources.get_datasource("simon/baby-yoda-segmentation-dataset", name="bucket-ds")
```

## Adding metadata

TODO WRITE

## Querying

We're striving to support a pandas-like

# Exporting to Voxel51

TODO WRITE

## Troubleshooting

It's VERY useful for us if you can turn on debug logging and report with that.
That way we can see the executing queries and their results

```python
import logging

logging.basicConfig(level=logging.DEBUG)
# Your code here
```


