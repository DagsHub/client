import pytest

from dagshub.data_engine import datasources
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.datasource import Datasource, DatasetState
from dagshub.data_engine.model.query_result import QueryResult
from tests.data_engine.util import add_string_fields


@pytest.fixture
def ds() -> Datasource:
    ds_state = datasources.DatasourceState(id=1, name="test-dataset", repo="kirill/repo")
    ds_state.path = "repo://kirill/repo/data/"
    yield Datasource(ds_state)


@pytest.fixture
def dataset_state(ds) -> DatasetState:
    add_string_fields(ds, "dataset_field")
    queried = ds["dataset_field"] == "aaa"

    state = DatasetState.from_dataset_query(
        dataset_id=100,
        dataset_name="dataset-name",
        datasource_id=ds.source.id,
        dataset_query=queried.serialize_gql_query_input(),
    )
    yield state


@pytest.fixture
def ds_with_dataset(ds, dataset_state) -> Datasource:
    ds.load_from_dataset_state(dataset_state)
    yield ds


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
