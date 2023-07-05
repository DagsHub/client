import pytest

from dagshub.data_engine.client.models import MetadataFieldSchema, MetadataFieldType, QueryResult, Datapoint
from dagshub.data_engine.model import datasources
from dagshub.data_engine.model.datasource import Datasource


@pytest.fixture
def ds():
    ds_state = datasources.DatasourceState(name="test-dataset", repo="kirill/repo")
    ds_state.metadata_fields = [
        MetadataFieldSchema("col1", MetadataFieldType.STRING, False),
        MetadataFieldSchema("col_int", MetadataFieldType.INTEGER, False),
    ]
    ds_state.path = "repo://kirill/repo/data/"
    yield Datasource(ds_state)


@pytest.fixture
def some_datapoints(ds):
    dps = []
    for i in range(5):
        dp = Datapoint(datasource=ds, path=f"dp_{i}", datapoint_id=i, metadata={})
        for j in range(5):
            dp.metadata[f"col{j}"] = i
        dps.append(dp)
    return dps


@pytest.fixture
def some_datapoint(some_datapoints):
    return some_datapoints[0]


@pytest.fixture
def query_result(ds, some_datapoints):
    qr = QueryResult(datasource=ds, _entries=some_datapoints)
    return qr
