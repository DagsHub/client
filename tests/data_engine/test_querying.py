import pytest

from dagshub.data_engine.model.datasource import (
    Datasource, Field,
)
from dagshub.data_engine.model.errors import WrongOrderError, DatasetFieldComparisonError, FieldNotFoundError
from dagshub.data_engine.model.query import DatasourceQuery, bytes_deserializer
from tests.data_engine.util import add_int_fields, add_string_fields, add_float_fields, add_boolean_fields, \
    add_blob_fields


def test_query_single_column(ds):
    add_int_fields(ds, "column1")
    column_name = "column1"
    ds2 = ds[column_name]
    assert type(ds2) is Datasource

    q = ds2.get_query()
    print(q.column_filter == column_name)


def test_simple_filter(ds):
    add_int_fields(ds, "column1")
    ds2 = ds[ds["column1"] > 5]
    q = ds2.get_query()
    expected = {"gt": {"data": {"field": "column1", "value": 5}}}
    assert q.to_dict() == expected


def test_versioning(ds):
    add_int_fields(ds, "x")
    add_int_fields(ds, "y")

    ds2 = ((ds[ds[Field("x", as_of_timestamp=123.99)] > 1]) &
           (ds[ds[Field("x", as_of_timestamp=345)] > 2]) |
           (ds[ds[Field("y", as_of_timestamp=789)] > 3])).\
        select([Field("y", as_of_timestamp=123), Field("x", as_of_timestamp=456, alias="y_t1")])
    q = ds2.get_query()
    expected = {'or': {'children': [{'and': {'children': [{'gt': {'data': {'field': 'x', 'as_of': 123, 'value': 1}}},
                                                          {'gt': {'data': {'field': 'x', 'as_of': 345, 'value': 2}}}],
                                             'data': None}},
                                    {'gt': {'data': {'field': 'y', 'as_of': 789, 'value': 3}}}], 'data': None}}
    assert q.to_dict() == expected

    expected_select = [{'name': 'y', 'asOf': 123}, {'name': 'x', 'asOf': 456, 'alias': 'y_t1'}]
    assert ds2._select == expected_select


def test_composite_filter(ds):
    add_int_fields(ds, "col1", "col2")
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
    add_int_fields(ds, "col1", "col2")
    add_string_fields(ds, "col3")
    add_float_fields(ds, "col4")
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
    add_int_fields(ds, "aaa", "bbb")
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
    add_int_fields(ds, "col1", "col2")
    # Have to do that because binary operators take precedence over numericals
    with pytest.raises(WrongOrderError):
        _ = ds["col1"] > 5 & ds["col2"] == 5


def test_error_on_ds_comparison(ds):
    add_int_fields(ds, "col1", "col2")
    with pytest.raises(DatasetFieldComparisonError):
        _ = ds["col1"] == ds["col2"]


def test_serialization(ds):
    add_int_fields(ds, "col1", "col2")
    add_string_fields(ds, "col3")
    add_float_fields(ds, "col4")
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
    add_int_fields(ds, "col1", "col2")
    add_string_fields(ds, "col3")
    add_float_fields(ds, "col4")
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
    add_string_fields(ds, "col1")
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
    add_string_fields(ds, "col1")
    add_int_fields(ds, "col2")
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
    add_string_fields(ds, "col1")
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
    add_string_fields(ds, "col1")
    add_int_fields(ds, "col2")
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
    add_string_fields(ds, "col1")
    add_int_fields(ds, "col2")
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
    add_string_fields(ds, "col1")
    queried = ds["col1"].is_null()
    expected = {
        "isnull": {"data": {"field": "col1", "value": ""}},
    }
    assert queried.get_query().to_dict() == expected


def test_isnull_int(ds):
    add_int_fields(ds, "col_int")
    queried = ds["col_int"].is_null()
    expected = {
        "isnull": {"data": {"field": "col_int", "value": int()}},
    }
    assert queried.get_query().to_dict() == expected


def test_isnull_serialization(ds):
    add_string_fields(ds, "col1")
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
    add_string_fields(ds, "col1")
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
    add_boolean_fields(ds, "col_bool")
    queried = ds["col_bool"] == False  # noqa
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


def test_throws_on_nonexistent_field(ds):
    add_int_fields(ds, "col1")
    with pytest.raises(FieldNotFoundError):
        _ = ds["nonexistent_field"] == 5


@pytest.mark.parametrize("string_value, expected", [
    ("b''", bytes()),
    ('b""', bytes()),
    ("b'abcd'", "abcd".encode("utf-8")),
    ("abcd", "abcd".encode("utf-8")),
    ("", bytes()),
])
def test_bytes_deserializer(string_value, expected):
    actual = bytes_deserializer(string_value)
    assert actual == expected


def test_blob_deserialization(ds):
    add_blob_fields(ds, "field_blob")
    queried = ds["field_blob"].is_null()

    serialized = {
        "filter": {
            "key": "field_blob",
            "value": "",
            "valueType": "BLOB",
            "comparator": "IS_NULL"
        }
    }
    deserialized = DatasourceQuery.deserialize(serialized)
    assert queried.get_query().serialize_graphql() == deserialized.serialize_graphql()


def test_sequential_querying(ds):
    add_blob_fields(ds, "col1")
    add_blob_fields(ds, "col2")
    queried = ds["col1"].is_null()
    queried2 = queried["col2"].is_null()

    expected = {
        "and": {
            "children": [
                {"isnull": {"data": {"field": "col1", "value": b""}}},
                {"isnull": {"data": {"field": "col2", "value": b""}}},
            ],
            "data": None,
        }
    }
    assert queried2.get_query().to_dict() == expected
