import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dagshub_annotation_converter.ir.image import IRSegmentationImageAnnotation

from dagshub.data_engine.annotation import MetadataAnnotations
from dagshub.data_engine.dtypes import MetadataFieldType, ReservedTags
from dagshub.data_engine.model import query_result
from dagshub.data_engine.model.datasource import Datasource
from tests.data_engine.util import add_metadata_field

_annotation_field_name = "annotation"
_dp_path = "data/sample_datapoint.jpg"
_annotation_hash = "annotation1"  # Corresponds to a resource JSON
_res_folder = Path(__file__).parent / "res"


def mock_annotation_query_result(
    ds: Datasource, annotation_field_name: str, dp_path: str, annotation_hash: str
) -> query_result.QueryResult:
    data = f"""
    {{
    "edges": [
        {{
            "node": {{
                "id": 1454819,
                "path": "{dp_path}",
                "createdAt": 0,
                "metadata": [
                    {{
                        "key": "{annotation_field_name}",
                        "timeZone": "",
                        "value": "{annotation_hash}",
                        "valueType": "BLOB",
                        "createdAt": 1751884461,
                        "__typename": "MetadataField"
                    }}
                ],
                "__typename": "Datapoint"
            }},
            "cursor": "1454819",
            "__typename": "DatapointsConnectionEdge"
        }}
    ],
    "queryDataTime": 1765705196
    }}
    """
    data_dict = json.loads(data)
    return query_result.QueryResult.from_gql_query(data_dict, ds)


def mock_get_blob(*args, **kwargs) -> bytes:
    download_url: str = args[0]
    blob_hash = download_url.split("/")[-1]
    blob_path = _res_folder / f"{blob_hash}.json"
    if not blob_path.exists():
        raise FileNotFoundError(f"Mock blob file not found: {blob_path}")
    return blob_path.read_bytes()


@pytest.fixture
def ds_with_document_annotation(ds, monkeypatch):
    add_metadata_field(
        ds,
        _annotation_field_name,
        MetadataFieldType.BLOB,
        tags={ReservedTags.ANNOTATION.value, ReservedTags.DOCUMENT.value},
    )

    ds.source.client.get_datapoints = MagicMock(
        return_value=mock_annotation_query_result(ds, _annotation_field_name, _dp_path, _annotation_hash)
    )

    monkeypatch.setattr(query_result, "_get_blob", mock_get_blob)

    yield ds


def test_annotation_with_document_are_parsed_as_annotation(ds_with_document_annotation):
    qr = ds_with_document_annotation.all()
    annotation: MetadataAnnotations = qr[0].metadata[_annotation_field_name]
    assert isinstance(annotation, MetadataAnnotations)
    # Check that the annotation got parsed correctly, the JSON should have one segmentation annotation in it
    assert len(annotation.annotations) == 1
    assert isinstance(annotation.annotations[0], IRSegmentationImageAnnotation)
