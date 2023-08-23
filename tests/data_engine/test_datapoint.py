import pytest
from dagshub.data_engine import dtypes
from dagshub.data_engine.model.datasource import MetadataContextManager


def test_getitem_metadata(some_datapoint):
    for key in some_datapoint.metadata:
        assert some_datapoint[key] == some_datapoint.metadata[key]

def test_add_annotation(ds):
    ctx = MetadataContextManager(ds)
    value = 5
    ctx.update_metadata("aaa", {"key1": dtypes.Int(value).as_annotation()})
    entries = ctx.get_metadata_entries()

    assert len(entries) == 1
    assert "annotation" in entries[0].tags

def test_add_random_tag(ds):
    ctx = MetadataContextManager(ds)
    value = 5
    tag_name = "random"
    ctx.update_metadata("aaa", {"V1.0.0": dtypes.Int(value).tag(tag_name)})
    entries = ctx.get_metadata_entries()

    assert len(entries) == 1
    assert tag_name in entries[0].tags

def test_add_wrong_random_tag(ds):
    ctx = MetadataContextManager(ds)
    value = 5
    tag_name = "annotation"
    with pytest.raises(Exception):
        ctx.update_metadata("aaa", {"V1.0.0": dtypes.Int(value).tag(tag_name)})
