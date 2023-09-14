import pytest
from dagshub.data_engine import dtypes
from dagshub.data_engine.client.models import MetadataFieldType
from dagshub.data_engine.model.datasource import MetadataContextManager, DatapointMetadataUpdateEntry


def test_getitem_metadata(some_datapoint):
    for key in some_datapoint.metadata:
        assert some_datapoint[key] == some_datapoint.metadata[key]

def test_add_annotation(ds):
    ctx = MetadataContextManager(ds)
    data = "aaa".encode()
    encoded_data = str(MetadataContextManager.wrap_bytes(data))

    ctx.update_metadata("aaa", {"key1": data})
    ctx.metadata_field("key1").set_annotation_field()

    entries = ctx.get_metadata_entries()

    assert len(entries) == 1
    assert ReservedTags.ANNOTATION.value in entries[0].tags # There should be a nicer way to check if an entry is an annotation

    expected = DatapointMetadataUpdateEntry("aaa", "key1", encoded_data, MetadataFieldType.BLOB, tags=[ReservedTags.ANNOTATION.value])
    assert entries == [expected]

# def test_add_random_tag(ds):
#     ctx = MetadataContextManager(ds)
#     value = 5
#     tag_name = "random"
#     ctx.update_metadata("aaa", {"V1.0.0": dtypes.Int(value).tag(tag_name)})
#     entries = ctx.get_metadata_entries()
#
#     assert len(entries) == 1
#     assert tag_name in entries[0].tags

def test_change_enrichement(ds):
    ctx = MetadataContextManager(ds)

    b1 = ds.source.metadata_field("Yuval's Annotations").set_type(dtypes.Int).set_annotation_field()
    b2 = ds.source.metadata_field("Yuval's Annotations").set_type(dtypes.String).set_prediction_field()
    b1(

    ds.update_fields([b1, b2])

    lst = [("field1", dtypes.Int), ("field2", dtypes.Int), ("field3", dtypes.Int)]

    ctx.update_metadata("aaa", {"Yuval's Annotations": "value"})

    # metadata field can also be manipulated after values are set
    # example:
    # ds.metadata_field("Yuval's Annotations").rename("Dean's annotations")

    entries = ctx.get_metadata_entries()
    # assert len(entries) == 1
    assert len(ds.fields()) == 1
    assert ds.fields()[0].is_annotation_field()

    # assert ReservedTags.ANNOTATION.value in entries[0].tags # There should be a nicer way to check if an entry is an annotation

# def test_add_wrong_random_tag(ds):
#     ctx = MetadataContextManager(ds)
#     value = 5
#     tag_name = "annotation"
#     with pytest.raises(Exception):
#         ctx.update_metadata("aaa", {"V1.0.0": dtypes.Int(value).tag(tag_name)})
