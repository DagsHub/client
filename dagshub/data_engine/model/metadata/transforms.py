import logging
from typing import List, TYPE_CHECKING, Dict

from dagshub.common.helpers import log_message
from dagshub.data_engine import dtypes
from dagshub.data_engine.dtypes import MetadataFieldType
from dagshub.data_engine.model.metadata.util import wrap_bytes
from dagshub.data_engine.model.metadata.validation import UploadingMetadataInfo, MAX_STRING_FIELD_LENGTH

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource, DatapointMetadataUpdateEntry

logger = logging.getLogger(__name__)


def _transform_strings_to_documents(ds: "Datasource", metadata: List["DatapointMetadataUpdateEntry"], field_name: str):
    log_message(f"Uploading field {field_name} as a document field due to long string values")
    ds.metadata_field(field_name).set_type(dtypes.Document).apply()
    for m in metadata:
        if m.key != field_name:
            continue
        m.valueType = MetadataFieldType.BLOB
        m.value = wrap_bytes(m.value.encode("utf-8"))


def run_preupload_transforms(
    ds: "Datasource",
    metadata: List["DatapointMetadataUpdateEntry"],
    precalculated_info: Dict[str, UploadingMetadataInfo],
):
    """
    Run transformations on metadata that should happen before uploading.

    Current transformations:
        - New string fields with large values get converted to a Document type
    """

    for info in precalculated_info.values():
        if (
            info.field_type == MetadataFieldType.STRING
            and info.existing_metadata_in_ds is None
            and len(info.longest_value) > MAX_STRING_FIELD_LENGTH
        ):
            _transform_strings_to_documents(ds, metadata, info.field_name)
