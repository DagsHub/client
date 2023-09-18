from dagshub.data_engine import dtypes
from dagshub.data_engine.dtypes import MetadataFieldType
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
    assert ReservedTags.ANNOTATION.value in entries[
        0].tags  # There should be a nicer way to check if an entry is an annotation

    expected = DatapointMetadataUpdateEntry("aaa", "key1", encoded_data, MetadataFieldType.BLOB,
                                            tags=[ReservedTags.ANNOTATION.value])
    assert entries == [expected]


def test_define_field(ds):
    ds.metadata_field("Yuval's Annotations").set_type(dtypes.Int()).set_annotation_field()

    assert len(ds.fields) == 1
    assert ds.fields[0].is_annotation()


def test_update_fields_in_batch(ds):
    ds.metadata_field("Yuval's Annotations").set_type(dtypes.Int()).set_annotation_field()
    ds.metadata_field("Ido's Annotations")

    # ds.update_fields() -> This is executed only in the e2e tests
    assert len(ds.fields) == 2
    assert ds.fields[0].is_annotation()
    assert not ds.fields[1].is_annotation()
