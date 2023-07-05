def test_getitem_metadata(some_datapoint):
    for key in some_datapoint.metadata:
        assert some_datapoint[key] == some_datapoint.metadata[key]
