import pytest

from dagshub.data_engine.model import datasources
from dagshub.data_engine.model.datasource import (
    Datasource,
)
from dagshub.data_engine.model.errors import WrongOrderError, DatasetFieldComparisonError


@pytest.fixture
def ds():
    yield Datasource(datasources.DatasourceState("test-dataset", "kirill/repo"))


def test_query_single_column(ds):
    column_name = "column1"
    ds2 = ds[column_name]
    assert type(ds2) is Datasource

    q = ds2.get_query()
    print(q._column_filter == column_name)


def test_simple_filter(ds):
    ds2 = ds[ds["column1"] > 5]
    q = ds2.get_query()
    expected = {"gt": {"data": {"field": "column1", "value": 5}}}
    assert q.to_dict() == expected


def test_composite_filter(ds):
    ds2 = ds[(ds["col1"] > 5) & (ds["col2"] <= 3)]
    expected = {
        "and": {
            "children": [
                {
                    "gt": {"data": {"field": "col1", "value": 5}},
                },
                {"le": {"data": {"field": "col2", "value": 3}}},
            ],
            "data": None,
        }
    }
    assert ds2.get_query().to_dict() == expected


def test_complexer_filter(ds):
    """
    This one has contains and some more composition
    """
    ds2 = ds[
        ((ds["col1"] > 5) & (ds["col2"] <= 3))
        | ds["col3"].contains("aaa")
        | (ds["col4"] != 5.0)
        ]
    expected = {
        "or": {
            "children": [
                {"ne": {"data": {"field": "col4", "value": 5.0}}},
                {
                    "or": {
                        "children": [
                            {
                                "and": {
                                    "children": [
                                        {
                                            "gt": {
                                                "data": {"field": "col1", "value": 5}
                                            },
                                        },
                                        {
                                            "le": {
                                                "data": {"field": "col2", "value": 3}
                                            },
                                        },
                                    ],
                                    "data": None,
                                }
                            },
                            {"contains": {"data": {"field": "col3", "value": "aaa"}}},
                        ],
                        "data": None,
                    }
                },
            ],
            "data": None,
        }
    }
    assert ds2.get_query().to_dict() == expected


def test_query_chaining(ds):
    ds2 = ds[ds["aaa"] > 5]
    ds3 = ds2[ds2["bbb"] <= 5]
    expected = {
        "and": {
            "children": [
                {"gt": {"data": {"field": "aaa", "value": 5}}},
                {"le": {"data": {"field": "bbb", "value": 5}}},
            ],
            "data": None,
        }
    }
    assert ds3.get_query().to_dict() == expected


def test_error_on_bad_order(ds):
    # Have to do that because binary operators take precedence over numericals
    with pytest.raises(WrongOrderError):
        _ = ds["col1"] > 5 & ds["col2"] == 5


def test_error_on_ds_comparison(ds):
    with pytest.raises(DatasetFieldComparisonError):
        _ = ds["col1"] == ds["col2"]


def test_serialization(ds):
    ds2 = ds[
        ((ds["col1"] > 5) & (ds["col2"] <= 3))
        | ds["col3"].contains("aaa")
        | (ds["col4"] != 5.0)
        ]
    expected = {
        "or": [
            {
                "or": [
                    {
                        "and": [
                            {
                                "filter": {
                                    "key": "col1",
                                    "value": str(5),
                                    "valueType": "INTEGER",
                                    "comparator": "GREATER_THAN",
                                }
                            },
                            {
                                "filter": {
                                    "key": "col2",
                                    "value": str(3),
                                    "valueType": "INTEGER",
                                    "comparator": "LESS_EQUAL_THAN",
                                }
                            }
                        ]
                    },
                    {
                        "filter": {
                            "key": "col3",
                            "value": "aaa",
                            "valueType": "STRING",
                            "comparator": "CONTAINS",
                        }
                    },
                ]
            },
            {
                "filter": {
                    "key": "col4",
                    "value": str(5.0),
                    "valueType": "FLOAT",
                    "comparator": "NOT_EQUAL"
                }
            }
        ]
    }
    assert ds2.get_query().serialize_graphql() == expected
