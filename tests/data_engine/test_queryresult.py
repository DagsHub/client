import math

from dagshub.data_engine.model.query_result import QueryResult


def test_getitem_path(query_result):
    dp = query_result["dp_0"]
    assert dp.datapoint_id == 0
    assert dp.path == "dp_0"


def test_getitem_index(query_result):
    dp = query_result[0]
    assert dp.datapoint_id == 0
    assert dp.path == "dp_0"


def test_getitem_slice_returns_query_result(query_result):
    qr = query_result[0 : len(query_result) : 2]
    assert type(qr) is QueryResult
    assert len(qr) == math.ceil(len(query_result) / 2)
    for i in range(len(qr)):
        assert qr[i].datapoint_id is query_result[i * 2].datapoint_id
