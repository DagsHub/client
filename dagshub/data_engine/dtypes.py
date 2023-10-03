import enum
from abc import ABCMeta
from typing import List


class ReservedTags(enum.Enum):
    ANNOTATION = "annotation"


# These are the base primitives that the data engine database is capable of storing
class MetadataFieldType(enum.Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BLOB = "BLOB"


# Inheritors of this ABC define custom types
# They are backed by a primitive type, but they also may have additional tags, describing specialized behavior
class DagshubDataType(metaclass=ABCMeta):
    """
    Attributes:
        backing_field_type: primitive type in the data engine database
        custom_tags: additional tags applied to this type
    """

    backing_field_type: MetadataFieldType = None
    custom_tags: List[str] = None


class Int(DagshubDataType):
    backing_field_type = MetadataFieldType.INTEGER


class String(DagshubDataType):
    backing_field_type = MetadataFieldType.STRING


class Blob(DagshubDataType):
    backing_field_type = MetadataFieldType.BLOB


class Float(DagshubDataType):
    backing_field_type = MetadataFieldType.FLOAT


class Bool(DagshubDataType):
    backing_field_type = MetadataFieldType.BOOLEAN


class LabelStudioAnnotation(DagshubDataType):
    backing_field_type = MetadataFieldType.BLOB
    custom_tags = [ReservedTags.ANNOTATION.value]


class Voxel51Annotation(DagshubDataType):
    backing_field_type = MetadataFieldType.BLOB
    custom_tags = [ReservedTags.ANNOTATION.value]
