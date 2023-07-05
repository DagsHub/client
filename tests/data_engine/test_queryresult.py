def test_getitem_path(query_result):
    dp = query_result["dp_0"]
    assert dp.datapoint_id == 0
    assert dp.path == "dp_0"


def test_getitem_index(query_result):
    dp = query_result[0]
    assert dp.datapoint_id == 0
    assert dp.path == "dp_0"
