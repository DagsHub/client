import pytest

from dagshub.data_engine import datasources
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.model.query_result import QueryResult


@pytest.fixture
def ds():
    ds_state = datasources.DatasourceState(name="test-dataset", repo="kirill/repo")
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
