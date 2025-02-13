import datetime
from typing import Type, Dict, Set, Any, Callable, Tuple, Optional

import dacite

from dagshub.common.util import wrap_bytes
from dagshub.data_engine.client.models import IntegrationStatus, DatasourceType, PreprocessingStatus
from dagshub.data_engine.dtypes import MetadataFieldType
from dagshub.data_engine.annotation import MetadataAnnotations

metadata_type_lookup = {
    int: MetadataFieldType.INTEGER,
    bool: MetadataFieldType.BOOLEAN,
    float: MetadataFieldType.FLOAT,
    str: MetadataFieldType.STRING,
    bytes: MetadataFieldType.BLOB,
    datetime.datetime: MetadataFieldType.DATETIME,
}


metadata_type_lookup_reverse: Dict[str, Type] = {}
for k, v in metadata_type_lookup.items():
    metadata_type_lookup_reverse[v.value] = k


def default_metadata_type_value(metadata_type: MetadataFieldType) -> Any:
    if metadata_type == MetadataFieldType.DATETIME:
        return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    else:
        return metadata_type_lookup_reverse[metadata_type.value]()


def timestamp_to_datetime(timestamp: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


dacite_config = dacite.Config(
    cast=[IntegrationStatus, DatasourceType, PreprocessingStatus, MetadataFieldType, Set],
    type_hooks={datetime.datetime: timestamp_to_datetime},
)


# Special handling of metadata conversion for certain classes
def _convert_annotation_metadata(annotation: MetadataAnnotations) -> Tuple[Optional[str], MetadataFieldType]:
    blob_value = annotation.to_ls_task()
    if blob_value is None:
        return None, MetadataFieldType.BLOB
    return wrap_bytes(blob_value), MetadataFieldType.BLOB


special_metadata_handlers: Dict[Type[Any], Callable[[Any], Tuple[Optional[str], MetadataFieldType]]] = {
    MetadataAnnotations: _convert_annotation_metadata,
}
