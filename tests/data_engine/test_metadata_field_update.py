import pytest

from dagshub.data_engine import dtypes
from dagshub.data_engine.dtypes import ReservedTags, MetadataFieldType
from tests.data_engine.util import add_int_fields


def test_have_to_set_type_on_new_field(ds):
    fb = ds.metadata_field("new_field")
    with pytest.raises(RuntimeError):
        fb.set_annotation()


def test_can_set_annotation_on_existing_field(ds):
    add_int_fields(ds, "field1")
    fb = ds.metadata_field("field1")
    fb.set_annotation()
    assert ReservedTags.ANNOTATION.value in fb.schema.tags


def test_builder_doesnt_change_original_field_schema(ds):
    add_int_fields(ds, "field1")
    fb = ds.metadata_field("field1").set_annotation()

    assert ReservedTags.ANNOTATION.value in fb.schema.tags
    assert ReservedTags.ANNOTATION.value not in ds.fields[0].tags


def test_annotation_type_sets_annotation_tag(ds):
    fb = ds.metadata_field("new_field").set_type(dtypes.LabelStudioAnnotation)
    assert fb.schema.valueType == MetadataFieldType.BLOB
    assert ReservedTags.ANNOTATION.value in fb.schema.tags
