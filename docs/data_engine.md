# Dagshub Data Engine documentation

## The overall idea

* You can define paths in your repo or bucket as datasources - collections of files and their metadata.
* A datasource is like a giant table of metadata, where one column (field) is the filepath and the other columns are
  metadata that
  either gets added automatically by DagsHub or that you can attach and modify whenever you want.
* DagsHub gives a pandas-like Python client to query this giant metadata table and return only matching files from your
  datasource.
* Further quality of life features will include things like versioning/auditing for the metadata, dataset curation, UI, data fetching optimizations, and more as we develop the product.


## Creating/Getting a datasource

### Creating

```python

from dagshub.data_engine import datasources

# Create a datasource from a connected storage bucket.
# You need to first connect the bucket to the repo using repo settings -> integrations.
ds = datasources.get_or_create("simon/baby-yoda-segmentation-dataset", "bucket-ds", "s3://data-bucket/prefix")

# OR
# Create a datasource from a path in the repo (last argument is the revision)
ds = datasources.get_or_create("simon/baby-yoda-segmentation-dataset", "path-ds", "path/to/dir", "main")
```

Shortly after creating the datasource, the DagsHub system will start scanning it for files and automatically adding some
metadata fields that we can infer automatically, such as file size.
You can start querying the datasource right away, but you'll see a warning message saying that the scan is still in
progress until it finishes adding all the files, so expect partial results.
You can start adding metadata before files get scanned, don't worry about waiting for the scan to finish before starting
metadata ingestion!

You can create as many datasources as you like, on as many paths as you like.
For example, you can create multiple different datasources pointing to the same bucket,
or to different subpaths in the same bucket, etc.
These different datasources will not be related to each other, each one will start clean and have a separate metadata
table
from all the other datasources, whether they point at the same bucket/path or not.

### Getting

Get all datasources in a repository:

```python
ds_list = datasources.get_datasources("simon/baby-yoda-segmentation-dataset")
```

To get a specific datasource use `datasources.get_datasource` function

```python

from dagshub.data_engine import datasources

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
  # Attach metadata to a single specific file in the datasource.
  # The first argument is the filepath to attach metadata to, **relative to the root of the datasource**.
  ctx.update_metadata("images/005.jpg", metadata)

  # Attach metadata to several files at once:
  ctx.update_metadata(["images/006.jpg","images/007.jpg"], metadata)
```

Once the code exits the `metadata_context()`, all of the metadata is uploaded to the server.

**Note:**  The datapoint should be the path of the file relative to the root of the data source. So if you have a repo
data source with path at `repo://simon/baby-yoda-segmentor/data` (starting from the data folder),
and you want to add metadata to a file located at `data/images/005.jpg` inside of the repo, then the path should
be `images/005.jpg`

### Schema and field types

Metadata dictionary is keyed by strings, currently acceptable value types are:

- Int
- Float
- Boolean
- String
- Blobs (need to be of type `bytes`)
- ** Please let us know about other metadata types you'd like to use and why **

We automatically infer the metadata types and create the schema when we first encounter a new metadata field name being
added.
So, while you don't need to declare a schema in advance, a typed schema gets created automatically, and you can't push
mismatched data types to an existing field.
We're considering allowing a more declarative typing system for this in the future.

### Adding metadata from a dataframe

You can also upload a whole dataframe as metadata:

```python
# Create a normal pandas dataframe (usually with pandas.read_csv, but done manually as an example here)
columns = ["path", "squirrel_detected"]
data = [["data/file1.png", True],
        ["data/file2.png", False]]
df = pd.DataFrame(data, columns=columns)

# Specify to our client which column identifies the file paths relative to the datasource root
ds.upload_metadata_from_dataframe(df, path_column="path")
```

`path_column` takes either the index or a name of the column to be used as the column with paths.
All other columns are considered metadata columns.
If `path_column` isn't specified, then the first column is considered as the path column.

## Getting data

At any point during working/querying, you can get the points that exist in the datasource with the current query

```python
# Get first 100 entries
head = ds.head(100)
# Get all entries
all = ds.all()
```

The returned objects carry the returned datapoints + metadata.
If you're more used to working with pandas dataframes, you can get a dataframe back by using the dataframe property:

```python
df = ds.head().dataframe
# Do pandas stuff with it next
```

### Blob fields

Blob fields are not downloaded by default, instead we return the hash of the field.

To get the contents of blob fields, you would usually want to iterate over the query result and run `get_blob`:
```python
for datapoint in ds.all():
  blob_bytes = datapoint.get_blob('blob-field-name')
```

See the docstring for `get_blob` for different options on whether to load the blob into memory permanently,
whether to cache it permanently on disk, etc.
By default, after running `get_blob` without custom arguments, it will get saved to disk, its bytes content will be
returned, and the contents of the `datapoint['blob-field-name']` metadata field will change from the hash of the blob
to its path on disk instead.

If instead you want to download blob fields for the entire dataset at once,
you can do that using the `get_blob_fields(*fields)` function of the QueryResult:

```python
df = ds.all().get_blob_fields("binary_1", "binary_2", load_into_memory=True).dataframe
# Now "binary_1" and "binary_2" fields have the paths to the downloaded blob files
```

This is **more efficient** than iterating over the datapoints one at a time, since we parallelize the downloads.

### Downloading files

You can download all the datapoints in the result of the query by calling the `download_files` function:

```python
qr = ds.all()
qr.download_files(target_dir=...)
```

If `target_dir` is not specified, downloads to the `~/dagshub/datasets/<user>/<repo>/<ds_id>` directory.
This is the same directory where we download files for voxel visualization

**NOTE**: if you're using a bucket as a datapoint source, and you have credentials for the S3/GCS client,
you can enable the bucket downloader, and the download functions will download the files using the bucket client,
instead of our servers

```python
from dagshub.common.download import enable_s3_bucket_downloader, enable_gcs_bucket_downloader

# S3
enable_s3_bucket_downloader()
# GCS
enable_gcs_bucket_downloader()

# You can also use a custom client, if the default auth is not set up
import boto3

client = boto3.client("s3", endpoint_url=...)
enable_s3_bucket_downloader(client)
```

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

Supported operands are: `==, !=, >, >=, <, <=, .contains(), .is_null(), is_not_null()`

To negate a condition use the complement `~` symbol: `df[~(<sub-query>)]`

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

- **You can only compare with primitives. Comparisons between fields are not allowed yet. Let us know if you need this.
  **
- The Python `in` syntax isn't supported: `"aaa" in df["col"]` doesn't work, you need to use `df["col"].contains("aaa")`
- Due to the order of execution for binary operators, if you use them, you need to wrap the other comparisons in
  parentheses
  (note the 2nd line in the example query)
- I don't recommend reusing the dataset variable for querying if you assign a result to a new query. This is undefined
  behavior that I did not test. Example below:

```python
# DON'T DO THIS
filtered_ds = ds[ds["episode"] > 5]
filtered_ds2 = filtered_ds[ds["has_baby_yoda"] == True]
```

Instead, it's preferred to have all the fields be addressed by the variable you address:

```python
# INSTEAD THIS IS PREFERRED
filtered_ds = ds[ds["episode"] > 5]
filtered_ds2 = filtered_ds[filtered_ds["has_baby_yoda"] == True]
```

## Saving queries

You can save the query you have on the datasource.
We call the combination of datasource + query a dataset.

To save a dataset call the `save_dataset` function, adding a name

```python
ds.save_dataset("my-cool-dataset")
```

In order to get the dataset back next time, do this:

```python

from dagshub.data_engine import datasets

ds = datasets.get_dataset("user/repo", "my-cool-dataset")
```

You'll get back the dataset and can continue working from where you left off


## Deleting a datasource

```python
ds.delete_source()
```

# Datasets and Dataloaders

To close the pipeline from a filtered dataset to beginning training, you can leverage datasets and dataloaders
from `torch` and `tensorflow` frameworks. The data is streamed using the DagsHub API.

## Sample Usage

```python
dataset_tr = query_result.as_ml_dataset(flavor='torch', strategy='background', processes=9000)
dataset_tf = query_result.as_ml_dataset('tensorflow', savedir='/tmp/.dataset/',
                                        metadata_columns=['file_depth', 'clf'], strategy='preload')

dataloader = query_result.as_ml_dataloader('torch', tensorizers='auto')
dataloader = query_result.as_ml_dataloader(dataset_tr, tensorizers='image')
dataloader = query_result.as_ml_dataloader('tensorflow', tensorizers=[lambda x: x])
dataloader = query_result.as_ml_dataloader(dataset_tf, tensorizers=['video', 'image', 'numeric'])

for X, y in dataloader:
# some training here
```

For details regarding potential kwarg options, run `help(<class>)` in a python runtime.

## Tensorizers

DataLoaders cannot return the entries by default. They need to be preprocessed and converted into a tensor before they
can be ingested by neural networks. To achieve this, the Dataset and DataLoader classes each expose tensorizer
functions, which can be passed as input to either `as_dataset` or `as_dataloader`.

These functions take as input either the raw data from the metadata or a `BufferedReader` containing file data and are
supposed to output Tensors.

Alternatively, you can either specify 'auto', where the client makes an attempt at guessing the datatype(s) and
tensorizing it. This works naively, checking just the file extension to see if there is a match. You can manually
specify a list of types ['image', 'audio', 'video'], and the client sequentially parses each column with the type.

## Multi/Label Columns

At the client-level, the data engine doesn't differentiate between input and label data. This is to support extensible
multimodal use cases with varying model I/O. You specify a list of output columns, the tensors for which you can allot
and accordingly train.

You can select which columns you would like to extract from the metadata by specifing a list of column names
to `metadata_columns`. The dataloaders return a list of all the tensorized entries.

## Streamed Data Download Strategies

1. Lazy: The client queries the DagsHub API as and when indices are requested. Intended for compute-restricted hardware.
2. Background: The client queries the DagsHub API using multithreading in the background, while returning the UI thread.
   If an item is requested that isn't already downloaded, the API is queried on the primary thread and returned. This is
   the ideal strategy.
3. Preload: The client queries the entire dataset, and only returns the primary thread once the download is completed.
   Intended for situations where avoiding dataloader delays is critical (for instance, GPU clusters where jobs have
   strict timeouts).

## Implementation Details + Quirks

`metadata_column` deciphers if a datatype is a file based on if the column starts with 'file_'. This is a temporary
solution, and will be replace by datasource-level metadata that is user customizable.

### PyTorch

1. Datsets extend the `torch.utils.data.Dataset` base class.
2. DataLoaders use the default `torch.utils.data.DataLoader`. Besides the `flavor` argument, calling `as_dataloader`
   proxies all DataLoader arguments to this class.

### TensorFlow

1. Datasets are created using generators, obtained by extending PyTorch's `torch.utils.data.DataLoader`.
2. DataLoaders extend `tf.keras.utils.Sequence`. Supported options are limited,

# Exporting to Voxel51

[This part is extremely experimental and only the happiest path is working there, expect to do manual cleanup sometimes]

We also added `fiftyone` to the dependencies, which allows you to load your data into a Voxel51 dataset and explore it
in voxel.
The datapoints will have all the metadata loaded and a new dataset named same as the datasource name will be created.

**All of the files in the queried subset will be downloaded to the local machine to `~/dagshub_datasets`**

Usage:

```python
voxel_session = ds.visualize()  # Will launch a new voxel instance and return back its session object
voxel_session.wait(-1)
```

We plan to expand the voxel functionality soon to integrate it much more with the Data Engine :)


# Contributing

Feel free to add whatever issues you get into the issue tracker on the repository

# Known issues

- No deleting of metadata yet
- Works only on data in the repository you specified. For now you can't create a datasource in one repo and use data
  from another repo
- The validation layer is very incomplete for now. That means that if you typo the repo name or a datapoints url, it'll
  still work
  probably
  (with unexpected results)

# Troubleshooting

It's VERY useful for us if you can turn on debug logging and report with that.
That way we can see the executing queries and their results

```python
import logging

logging.basicConfig(level=logging.DEBUG)
# Your code after
```

### Visualizing with voxel raises errors about javascript or nonserializable strawberry annotations

Make sure that you do a force reinstall of voxel, some of the dependencies aren't getting updated in order

```bash
$ pip install --upgrade --force-reinstall fiftyone
```


