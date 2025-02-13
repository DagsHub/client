from typing import Optional, Set

from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType, ReservedTags
from dagshub.data_engine.model.datasource import Datasource


def add_int_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.INTEGER)


def add_float_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.FLOAT)


def add_string_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.STRING)


def add_blob_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.BLOB)


def add_boolean_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.BOOLEAN)


def add_document_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.BLOB, tags={ReservedTags.DOCUMENT.value})


def add_datetime_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.DATETIME)


def add_annotation_fields(ds: Datasource, *names: str):
    for name in names:
        add_metadata_field(ds, name, MetadataFieldType.BLOB, tags={ReservedTags.ANNOTATION.value})


def add_metadata_field(
    ds: Datasource,
    name: str,
    value_type: MetadataFieldType,
    is_multiple: bool = False,
    tags: Optional[Set[str]] = None,
):
    if tags is None:
        tags = set()
    field = MetadataFieldSchema(name, value_type, is_multiple, tags)
    ds.source.metadata_fields.append(field)
