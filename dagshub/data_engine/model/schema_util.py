import datetime
from typing import Type, Dict, Set

import dacite

from dagshub.data_engine.client.models import IntegrationStatus, DatasourceType, PreprocessingStatus
from dagshub.data_engine.dtypes import MetadataFieldType

metadataTypeLookup = {
    int: MetadataFieldType.INTEGER,
    bool: MetadataFieldType.BOOLEAN,
    float: MetadataFieldType.FLOAT,
    str: MetadataFieldType.STRING,
    bytes: MetadataFieldType.BLOB,
    datetime.datetime: MetadataFieldType.DATETIME,
}

metadataTypeLookupReverse: Dict[str, Type] = {}
for k, v in metadataTypeLookup.items():
    metadataTypeLookupReverse[v.value] = k

dacite_config = dacite.Config(cast=[IntegrationStatus, DatasourceType, PreprocessingStatus, MetadataFieldType, Set])
