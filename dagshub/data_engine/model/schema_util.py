from typing import Type, Dict

from dagshub.data_engine.dtypes import MetadataFieldType

metadataTypeLookup = {
    int: MetadataFieldType.INTEGER,
    bool: MetadataFieldType.BOOLEAN,
    float: MetadataFieldType.FLOAT,
    str: MetadataFieldType.STRING,
    bytes: MetadataFieldType.BLOB,
}

metadataTypeLookupReverse: Dict[str, Type] = {}
for k, v in metadataTypeLookup.items():
    metadataTypeLookupReverse[v.value] = k
