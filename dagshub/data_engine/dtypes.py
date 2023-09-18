import enum


class MetadataFieldType(enum.Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BLOB = "BLOB"


class DagshubDataType:
    _corresponding_field_type = None

    def get_corresponding_field_type(self):
        return self._corresponding_field_type

    pass


class Int(DagshubDataType):
    _corresponding_field_type = MetadataFieldType.INTEGER
    pass


class String(DagshubDataType):
    _corresponding_field_type = MetadataFieldType.STRING
    pass


class Blob(DagshubDataType):
    _corresponding_field_type = MetadataFieldType.BLOB
    pass


class Float(DagshubDataType):
    _corresponding_field_type = MetadataFieldType.FLOAT
    pass


class Bool(DagshubDataType):
    _corresponding_field_type = MetadataFieldType.BOOLEAN
    pass
