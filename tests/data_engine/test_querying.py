import pytest

from dagshub.data_engine.model.datasource import (
    Datasource,
)
from dagshub.data_engine.model.errors import WrongOrderError, DatasetFieldComparisonError
from dagshub.data_engine.model.query import DatasourceQuery


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
        | (ds["col4"] == 5.0)
        ]
    expected = {
        "or": {
            "children": [
                {"eq": {"data": {"field": "col4", "value": 5.0}}},
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
        | (ds["col4"] == 5.0)
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
                    "comparator": "EQUAL"
                }
            }
        ]
    }
    assert ds2.get_query().serialize_graphql() == expected


def test_deserialization_complex(ds):
    queried = ds[
        ((ds["col1"] > 5) & (ds["col2"] <= 3))
        | ds["col3"].contains("aaa")
        | (ds["col4"] == 5.0)
        ]
    serialized = {
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
                    "comparator": "EQUAL"
                }
            }
        ]
    }

    deserialized = DatasourceQuery.deserialize(serialized)
    assert deserialized.serialize_graphql() == queried.get_query().serialize_graphql()


def test_not_equals(ds):
    queried = ds[ds["col1"] != "aaa"]
    expected = {
        "not": {
            "children": [
                {
                    "eq": {"data": {"field": "col1", "value": "aaa"}}
                }
            ],
            "data": None
        }
    }
    assert queried.get_query().to_dict() == expected


def test_not_and(ds):
    queried = ds[~((ds["col1"] == "aaa") & (ds["col2"] > 5))]
    expected = {
        "not": {
            "children": [
                {
                    "and": {
                        "children": [
                            {"eq": {"data": {"field": "col1", "value": "aaa"}}},
                            {"gt": {"data": {"field": "col2", "value": 5}}},
                        ],
                        "data": None
                    }
                }
            ],
            "data": None
        }
    }
    assert queried.get_query().to_dict() == expected


def test_not_serialization(ds):
    queried = ds[ds["col1"] != "aaa"]
    expected = {
        "filter": {
            "key": "col1",
            "value": "aaa",
            "valueType": "STRING",
            "comparator": "EQUAL"
        },
        "not": True
    }
    assert queried.get_query().serialize_graphql() == expected


def test_nand_serialization(ds):
    queried = ds[~((ds["col1"] == "aaa") & (ds["col2"] > 5))]
    expected = {
        "and": [
            {"filter": {
                "key": "col1",
                "value": "aaa",
                "valueType": "STRING",
                "comparator": "EQUAL"
            }},
            {"filter": {
                "key": "col2",
                "value": str(5),
                "valueType": "INTEGER",
                "comparator": "GREATER_THAN"
            }}
        ],
        "not": True
    }
    assert queried.get_query().serialize_graphql() == expected


def test_nand_deserialization(ds):
    queried = ds[~((ds["col1"] == "aaa") & (ds["col2"] > 5))]
    serialized = {
        "and": [
            {"filter": {
                "key": "col1",
                "value": "aaa",
                "valueType": "STRING",
                "comparator": "EQUAL"
            }},
            {"filter": {
                "key": "col2",
                "value": str(5),
                "valueType": "INTEGER",
                "comparator": "GREATER_THAN"
            }}
        ],
        "not": True
    }
    deserialized = DatasourceQuery.deserialize(serialized)
    assert queried.get_query().serialize_graphql() == deserialized.serialize_graphql()


def test_isnull(ds):
    queried = ds["col1"].is_null()
    expected = {
        "isnull": {"data": {"field": "col1", "value": ""}},
    }
    assert queried.get_query().to_dict() == expected


def test_isnull_int(ds):
    queried = ds["col_int"].is_null()
    expected = {
        "isnull": {"data": {"field": "col_int", "value": int()}},
    }
    assert queried.get_query().to_dict() == expected


def test_isnull_serialization(ds):
    queried = ds["col1"].is_null()
    expected = {
        "filter": {
            "key": "col1",
            "value": "",
            "valueType": "STRING",
            "comparator": "IS_NULL"
        }
    }

    assert queried.get_query().serialize_graphql() == expected


def test_isnull_deserialization(ds):
    queried = ds["col1"].is_null()
    serialized = {
        "filter": {
            "key": "col1",
            "value": "",
            "valueType": "STRING",
            "comparator": "IS_NULL"
        }
    }
    deserialized = DatasourceQuery.deserialize(serialized)
    assert queried.get_query().serialize_graphql() == deserialized.serialize_graphql()


def test_isnull_raises_not_on_field(ds):
    with pytest.raises(RuntimeError):
        ds.is_null()


def test_false_deserialization(ds):
    queried = ds["col_bool"] == False
    serialized = {
        "filter": {
            "key": "col_bool",
            "value": "False",
            "valueType": "BOOLEAN",
            "comparator": "EQUAL"
        }
    }
    deserialized = DatasourceQuery.deserialize(serialized)
    assert queried.get_query().serialize_graphql() == deserialized.serialize_graphql()
