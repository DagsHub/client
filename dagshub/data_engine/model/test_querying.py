import pytest

from dagshub.data_engine.model import datasources
from dagshub.data_engine.model.dataset import Dataset, WrongOrderError, DatasetFieldComparisonError


@pytest.fixture
def ds():
    yield datasources.from_repo("test-dataset", "kirill/repo", ".")


def test_query_single_column(ds):
    column_name = "column1"
    ds2 = ds[column_name]
    assert type(ds2) is Dataset

    q = ds2.get_query()
    print(q._column_filter == column_name)


def test_simple_filter(ds):
    ds2 = ds[ds["column1"] > 5]
    q = ds2.get_query()
    expected = {"gt": {"data": {"field": "column1", "value": 5}}}
    assert q.to_dict() == expected


def test_composite_filter(ds):
    ds2 = ds[(ds["col1"] > 5) & (ds["col2"] <= 3)]
    expected = {"and": {
        "children": [
            {
                "gt": {"data": {"field": "col1", "value": 5}},
            },
            {
                "le": {"data": {"field": "col2", "value": 3}}
            }
        ],
        "data": None
    }}
    assert ds2.get_query().to_dict() == expected


def test_error_on_bad_order(ds):
    # Have to do that because binary operators take precedence over numericals
    with pytest.raises(WrongOrderError):
        _ = ds["col1"] > 5 & ds["col2"] == 5


def test_error_on_ds_comparison(ds):
    with pytest.raises(DatasetFieldComparisonError):
        _ = ds["col1"] == ds["col2"]
