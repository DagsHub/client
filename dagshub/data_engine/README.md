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

Get all datasources in a repository:

```python
ds_list = datasources.get_datasources("simon/baby-yoda-segmentation-dataset")
```

To get a specific datasource use `datasources.get_datasource()` function

```python
from dagshub.data_engine.model import datasources

# Can accept either name argument, or id argument
ds = datasources.get_datasource("simon/baby-yoda-segmentation-dataset", name="bucket-ds")
```

## Adding metadata

Before you can start querying and playing with data, you need to first add metadata.

To add metadata to a file path (we call them datapoints), we provide a `metadata_context` on the datasource object:

```python
with ds.metadata_context() as ctx:
  metadata = {
    "episode": 5,
    "has_baby_yoda": True,
  }
  ctx.update_metadata("images/005.jpg", metadata)
```

The first argument for `update_metadata()` can be a single datapoint, or an array of multiple datapoints if you want to
add metadata to multiples.

Metadata dictionary is keyed by strings, acceptable value types are:

- Int
- Float
- Boolean
- String

Once the code exits the `metadata_context()`, all of the metadata is uploaded to the server

**Note:**  The datapoint should be the path of the file relative to the root of the data source. So if you have a repo
data source with path at `repo://simon/baby-yoda-segmentor/data` (starting from the data folder),
and you want to add metadata to a file located at `data/images/005.jpg` inside of the repo, then the path should
be `images/005.jpg`

### Adding metadata from a dataframe

You can also upload a whole dataframe as metadata:

```python
data = {
  "path": {"data/file1.png", "data/file2.png"},
  "has_squirrel": {True, False},
}
df = pd.DataFrame(data)

ds.upload_metadata_from_dataframe(df, path_column="path")
```

`path_column` takes either the index or a name of the column to be used as the column with paths.
All other columns are considered metadata columns.
If `path_column` isn't specified, then the first column is considered as the path column.

## Getting data

At any point during working/querying, you can get the points that exist in the datasource with the current query

```python
# Get first 100 entries
head = ds.head()
# Get all entries
all = ds.all()
```

The returned objects carry the returned datapoints + metadata. If you're more used to working pandas dataframes, you can
get a dataframe back by using the dataframe property:

```python
df = ds.head().dataframe
# Do pandas stuff with it next
```

**Caveat:** Since we don't have initial datapoint ingestion for now, the only datapoints you get back are the ones
you've uploaded the metadata on

## Querying

We're striving to support
a [pandas-like syntax for querying](https://stackoverflow.com/questions/15315452/selecting-with-complex-criteria-from-pandas-dataframe)

### Example query:

```python
q1 = ds["episode"] > 5
q2 = (ds["episode"] == 0) & (ds["has_baby_yoda"] == True)
df = ds[q1 | q2].all().dataframe

# Will return a pandas dataframe with the files and the metadata
```

The dataframe returned by `.dataframe` has a `dagshub_download_url` field with the URL to the download the file.
This way if your ML framework supports loading files from dataframes with urls, you can pass the dataframe to them.

Supported operands are: `==, >, >=, <, <=, .contains()` (We're working on adding `!=`)

Queries can be composed logically via binary and/or operators `&` and `|`. If you do a subquery, it is considered to be
composed with and

```python
# This:
ds2 = ds[ds["episode"] > 5]
ds3 = ds2[ds2["has_baby_yoda"] == True]

# Is the same as this:
ds2 = ds[(ds["episode"] > 5) & (ds["has_baby_yoda"] == True)]
```

### Caveats:

- You can only compare with primitives. Comparisons between columns are not allowed
- `"aaa" in df["col"]` doesn't work, you need to use `df["col"].contains("aaa")`
- Due to the order of execution for binary operators, if you use them, you need to wrap the other comparisons in
  parentheses
  (note the 2nd line in the example query)
- I don't recommend reusing the dataset variable for querying if you assign a result to a new query. This is undefined
  behavior that I did not test

Example:

```python
filtered_ds = ds[ds["episode"] > 5]
filtered_ds2 = filtered_ds[ds["has_baby_yoda"] == True]
```

Instead, it's preferred to have all the columns be addressed by the variable you address:

```python
filtered_ds = ds[ds["episode"] > 5]
filtered_ds2 = filtered_ds[filtered_ds["has_baby_yoda"] == True]
```

# Exporting to Voxel51

[This part is extremely experimental and only the happiest path is working there, expect to do manual cleanup sometimes]

We also added `fiftyone` to the dependencies, which allows you to load your data into a Voxel51 dataset and explore it
in voxel.
The datapoints will have all the metadata loaded and a new dataset named same as the datasource name will be created.

**All of the files in the queried subset will be downloaded to the local machine to `~/dagshub_datasets`**

Usage:

```python
import fiftyone as fo

voxel_dataset = ds.to_voxel51_dataset()
sess = fo.launch_app(voxel_dataset)  # Will open a new voxel window
sess.wait()
```

We plan to expand the voxel functionality soon to integrate it much more with the Data Engine :)

## Deleting a datasource

```python
ds.delete_source()
```

## Contributing

Feel free to add whatever issues you get into the issue tracker on the repository

## Known issues

- No deleting of metadata
- Works only on data in the repository you specified. For now you can't create a datasource in one repo and use data
  from another repo
- The validation layer is very incomplete for now. That means that if you typo the repo name or a datapoints url, it'll
  still work
  probably
  (with unexpected results)
- Voxel integration shoves all data into `~/dagshub_datasets` with no concern for whatever files are already there (
  wastes bandwidth + space)

## Troubleshooting

It's VERY useful for us if you can turn on debug logging and report with that.
That way we can see the executing queries and their results

```python
import logging

logging.basicConfig(level=logging.DEBUG)
# Your code after
```


