from dataclasses import dataclass, field
from typing import Set, Dict, Optional

from dataclasses_json import DataClassJsonMixin, config, LetterCase

from dagshub.common.util import exclude_if_none
from dagshub.data_engine.dtypes import MetadataFieldType


@dataclass
class DatasourceFieldInfo:
    """
    Utility class for add_metadata that caches a bunch of relevant information about the datasource fields,
    to prevent constant lookups
    """

    multivalue_fields: Set[str]
    field_value_types: Dict[str, MetadataFieldType]
    document_fields: Set[str]


@dataclass
class DatapointMetadataUpdateEntry(DataClassJsonMixin):
    url: str
    key: str
    value: str
    valueType: MetadataFieldType = field(metadata=config(encoder=lambda val: val.value))
    allowMultiple: bool = False
    timeZone: Optional[str] = field(
        default=None, metadata=config(exclude=exclude_if_none, letter_case=LetterCase.CAMEL)
    )
