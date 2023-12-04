Data Engine (Dataset Management)
========================================

+++++++++++++
Datasources
+++++++++++++

The main class used to interact with the Data Engine is :class:`.Datasource`

Here are functions that you can use to get and create datasources on your repository:

.. automodule:: dagshub.data_engine.datasources
    :members:

+++++++++++
Datasets
+++++++++++

Datasets are "save states" of Datasources with an already preapplied query.
They can be stored on DagsHub and retrieved later by you or anybody else.

To save a dataset, apply a query to a datasource then call
:func:`~dagshub.data_engine.model.datasource.Datasource.save_dataset`

.. automodule:: dagshub.data_engine.datasets
    :members:

++++++++++++++++++++++++++
Data Engine Structures
++++++++++++++++++++++++++

.. toctree::
    :titlesonly:

    datasource
    query_result
    datapoint
    data_types
