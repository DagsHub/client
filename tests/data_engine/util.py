from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType
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


def add_metadata_field(ds: Datasource, name: str, value_type: MetadataFieldType, is_multiple: bool = False):
    field = MetadataFieldSchema(name, value_type, is_multiple)
    ds.source.metadata_fields.append(field)
