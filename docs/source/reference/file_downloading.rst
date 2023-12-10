File Downloading
==================

Streaming files from the repository (``dagshub.streaming``)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. automodule:: dagshub.streaming
    :members:

Direct download from connected buckets
++++++++++++++++++++++++++++++++++++++++

These functions allow you to enable a client-downloader for a bucket you have connected to DagsHub.

When you download a file from a connected bucket, the request usually has to go through our server.
This function allows you to skip the middleman and download the file directly from the bucket.
This could save you time and money, if the downloading machine is colocated with the buckets.

The functions that work with these downloaders are:

- :func:`Datasource.visualize() <dagshub.data_engine.model.datasource.Datasource.visualize>`
- :func:`Datasource.to_voxel51_dataset() <dagshub.data_engine.model.datasource.Datasource.to_voxel51_dataset>`
- :func:`QueryResult.visualize() <dagshub.data_engine.model.query_result.QueryResult.visualize>`
- :func:`QueryResult.to_voxel51_dataset() <dagshub.data_engine.model.query_result.QueryResult.to_voxel51_dataset>`
- :func:`QueryResult.download_files() <dagshub.data_engine.model.query_result.QueryResult.download_files>`
- :func:`Datapoint.download_file() <dagshub.data_engine.model.datapoint.Datapoint.download_file>`

.. autofunction:: dagshub.common.download.enable_s3_bucket_downloader
.. autofunction:: dagshub.common.download.enable_gcs_bucket_downloader
.. autofunction:: dagshub.common.download.enable_azure_container_downloader
.. autofunction:: dagshub.common.download.add_bucket_downloader
