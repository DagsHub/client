import enum
from abc import ABCMeta
from typing import Set


class ReservedTags(enum.Enum):
    """:meta private:"""
    ANNOTATION = "annotation"


# These are the base primitives that the data engine database is capable of storing
class MetadataFieldType(enum.Enum):
    """
    Backing types in the Data Engine's database
    """
    BOOLEAN = "BOOLEAN"
    """Python's ``bool``"""
    INTEGER = "INTEGER"
    """Python's ``int``"""
    FLOAT = "FLOAT"
    """Python's ``float``"""
    STRING = "STRING"
    """Python's ``str``"""
    BLOB = "BLOB"
    """Python's ``bytes``"""


class DagshubDataType(metaclass=ABCMeta):
    """
    Inheritors of this ABC define custom types

    They are backed by a primitive type, but they also may have additional tags, which we use to enhance the experience.

    Attributes:
        backing_field_type: primitive type in the data engine database
        custom_tags: additional tags applied to this type
    """

    backing_field_type: MetadataFieldType = None
    custom_tags: Set[str] = None


class Int(DagshubDataType):
    """Basic python ``int``"""
    backing_field_type = MetadataFieldType.INTEGER


class String(DagshubDataType):
    """Basic python ``str``"""
    backing_field_type = MetadataFieldType.STRING


class Blob(DagshubDataType):
    """
    Basic python ``bytes``

    .. note::
        DagsHub doesn't return the blob fields by default, instead returning their hashes.
        Check out :func:`Datapoint.get_blob() <dagshub.data_engine.model.datapoint.Datapoint.get_blob>`
        to learn how to download the blob value.
    """
    backing_field_type = MetadataFieldType.BLOB


class Float(DagshubDataType):
    """
    Basic python ``float``
    """
    backing_field_type = MetadataFieldType.FLOAT


class Bool(DagshubDataType):
    """
    Basic python ``bool``
    """
    backing_field_type = MetadataFieldType.BOOLEAN


class LabelStudioAnnotation(DagshubDataType):
    """
    LabelStudio annotation. Backing type is blob.
    Has the annotation tag set.
    """
    backing_field_type = MetadataFieldType.BLOB
    custom_tags = {ReservedTags.ANNOTATION.value}


class Voxel51Annotation(DagshubDataType):
    """
    Voxel51 annotation. Backing type is blob.
    Has the annotation tag set.
    """
    backing_field_type = MetadataFieldType.BLOB
    custom_tags = {ReservedTags.ANNOTATION.value}
