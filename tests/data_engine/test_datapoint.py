import pytest
from dagshub.data_engine import dtypes
from dagshub.data_engine.dtypes import ReservedTags
from dagshub.data_engine.client.models import MetadataFieldType
from dagshub.data_engine.model.datasource import MetadataContextManager, DatapointMetadataUpdateEntry


def test_getitem_metadata(some_datapoint):
    for key in some_datapoint.metadata:
        assert some_datapoint[key] == some_datapoint.metadata[key]

def test_add_annotation(ds):
    ctx = MetadataContextManager(ds)
    data = "aaa".encode()
    encoded_data = str(MetadataContextManager.wrap_bytes(data))

    ctx.update_metadata("aaa", {"key1": dtypes.Blob(data).as_annotation()})
    entries = ctx.get_metadata_entries()

    assert len(entries) == 1
    assert ReservedTags.ANNOTATION.value in entries[0].tags # There should be a nicer way to check if an entry is an annotation

    expected = DatapointMetadataUpdateEntry("aaa", "key1", encoded_data, MetadataFieldType.BLOB, tags=[ReservedTags.ANNOTATION.value])
    assert entries == [expected]

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
