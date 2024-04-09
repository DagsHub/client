from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Dict

from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import DatapointMetadataUpdateEntry, Datasource

MAX_STRING_FIELD_LENGTH = 512


@dataclass
class UploadingMetadataInfo:
    field_name: str
    """Name of the field"""
    field_type: MetadataFieldType
    """Type of the metadata in the field"""
    existing_metadata_in_ds: Optional[MetadataFieldSchema] = None
    """Info about the existing field in the datasource. If None, this is a new field"""
    longest_value: str = ""
    """For string fields - longest value"""


class MultipleDataTypesUploadedError(Exception):
    def __init__(self, field_name: str, orig_type: MetadataFieldType, other_type: MetadataFieldType):
        self.field_name = field_name
        self.orig_type = orig_type
        self.other_type = other_type

    def __str__(self):
        return (
            f"Tried to upload data with different values for field {self.field_name}. "
            f"Original type is {self.orig_type.value}, tried to upload {self.other_type.value}"
        )


class StringFieldValueTooLongError(Exception):
    def __init__(self, field_name: str, value: str):
        self.field_name = field_name
        self.value = value

    def __str__(self):
        return (
            f"Trying to insert a value into a string field {self.field_name} "
            f"that is longer than the maximum allowed length of {MAX_STRING_FIELD_LENGTH}.\n"
            "If you need to upload large text, use a document field instead.\n"
            f"Value that was over the limit: {self.value}"
        )


def precalculate_metadata_info(
    ds: "Datasource", metadata: List["DatapointMetadataUpdateEntry"]
) -> Dict[str, UploadingMetadataInfo]:
    """
    Calculates information about uploading metadata + checks for accidental mixing of data types along the way
    """
    res = {}
    for m in metadata:
        if m.key not in res:
            info = UploadingMetadataInfo(
                field_name=m.key,
                field_type=m.valueType,
                existing_metadata_in_ds=next(filter(lambda f: f.name == m.key, ds.fields), None),
            )
            res[m.key] = info

            if info.existing_metadata_in_ds is not None:
                # Check that user is not uploading other type of value accidentally
                if info.existing_metadata_in_ds.valueType != m.valueType:
                    raise MultipleDataTypesUploadedError(m.key, info.existing_metadata_in_ds.valueType, m.valueType)

        else:
            info = res[m.key]

            if info.field_type != m.valueType:
                raise MultipleDataTypesUploadedError(m.key, info.field_type, m.valueType)

        if info.field_type == MetadataFieldType.STRING:
            info.longest_value = info.longest_value if len(info.longest_value) > len(m.value) else m.value
    return res


def validate_uploading_metadata(precalculated_info: Dict[str, UploadingMetadataInfo]):
    """
    Run client-side validations on uploading metadata

    Current validations:
        - String fields can't be too big, but only if it's being inserted into an existing field
            New fields are OK, they will be transformed into blobs later during the transforms
        - [Run during precalculation] Can't upload data of different types
        - [Run during precalculation] Can't upload data of a type different to the one already in datasource
    """
    for info in precalculated_info.values():
        if (
            info.field_type == MetadataFieldType.STRING
            and info.existing_metadata_in_ds is not None
            and len(info.longest_value) > MAX_STRING_FIELD_LENGTH
        ):
            raise StringFieldValueTooLongError(info.field_name, info.longest_value)
