import enum
class MetadataFieldType(enum.Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BLOB = "BLOB"

class DagshubDataType:
    def get_corressponding_field_type(self):
        return self._corressponding_field_type
    pass


class Int(DagshubDataType):
    _corressponding_field_type = MetadataFieldType.INTEGER
    pass


class String(DagshubDataType):
    _corressponding_field_type = MetadataFieldType.STRING
    pass


class Blob(DagshubDataType):
    _corressponding_field_type = MetadataFieldType.BLOB
    pass


class Float(DagshubDataType):
    _corressponding_field_type = MetadataFieldType.FLOAT
    pass


class Bool(DagshubDataType):
    _corressponding_field_type = MetadataFieldType.BOOLEAN
    pass
