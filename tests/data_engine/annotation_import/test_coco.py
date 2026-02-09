import datetime
import json
from pathlib import PurePosixPath
from unittest.mock import patch, PropertyMock

import pytest
from dagshub_annotation_converter.ir.image import (
    IRBBoxImageAnnotation,
    IRSegmentationImageAnnotation,
    IRSegmentationPoint,
    CoordinateStyle,
)

from dagshub.data_engine.annotation.importer import AnnotationImporter
from dagshub.data_engine.annotation.metadata import MetadataAnnotations
from dagshub.data_engine.client.models import MetadataSelectFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType, ReservedTags
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.query_result import QueryResult


@pytest.fixture(autouse=True)
def mock_source_prefix(ds):
    with patch.object(type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath()):
        yield


# --- COCO import ---


def test_import_coco_from_file(ds, tmp_path):
    coco_file = tmp_path / "annotations.json"
    coco_file.write_text(json.dumps(_make_coco_json()))

    importer = AnnotationImporter(ds, "coco", coco_file, load_from="disk")
    result = importer.import_annotations()

    assert "image1.jpg" in result
    assert len(result["image1.jpg"]) == 1
    assert isinstance(result["image1.jpg"][0], IRBBoxImageAnnotation)


def test_convert_image_to_ls_tasks(ds, tmp_path, mock_dagshub_auth):
    importer = AnnotationImporter(ds, "coco", tmp_path / "ann.json", load_from="disk")
    bbox = IRBBoxImageAnnotation(
        filename="test.jpg",
        categories={"cat": 1.0},
        top=0.1, left=0.1, width=0.2, height=0.2,
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.NORMALIZED,
    )

    tasks = importer.convert_to_ls_tasks({"test.jpg": [bbox]})

    assert "test.jpg" in tasks
    task_json = json.loads(tasks["test.jpg"])
    assert "annotations" in task_json


# --- add_coco_annotation ---


def test_add_coco_annotation(ds, mock_dagshub_auth):
    dp = Datapoint(datasource=ds, path="test.jpg", datapoint_id=0, metadata={})
    meta_ann = MetadataAnnotations(datapoint=dp, field="ann")
    meta_ann.add_coco_annotation(json.dumps(_make_coco_json()))

    assert len(meta_ann.annotations) == 1
    assert isinstance(meta_ann.annotations[0], IRBBoxImageAnnotation)
    assert meta_ann.annotations[0].filename == "test.jpg"


def test_add_coco_annotation_segmentation(ds, mock_dagshub_auth):
    dp = Datapoint(datasource=ds, path="test.jpg", datapoint_id=0, metadata={})
    coco = {
        "categories": [{"id": 1, "name": "dog"}],
        "images": [{"id": 1, "width": 640, "height": 480, "file_name": "img.jpg"}],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [[10, 20, 30, 40, 50, 60]]}
        ],
    }
    meta_ann = MetadataAnnotations(datapoint=dp, field="ann")
    meta_ann.add_coco_annotation(json.dumps(coco))

    assert len(meta_ann.annotations) == 1


# --- _resolve_annotation_field ---


def test_resolve_explicit(ds):
    qr = _make_qr(ds, [], ann_field="my_ann")
    assert qr._resolve_annotation_field("explicit") == "explicit"


def test_resolve_auto(ds):
    qr = _make_qr(ds, [], ann_field="my_ann")
    assert qr._resolve_annotation_field(None) == "my_ann"


def test_resolve_no_fields(ds):
    qr = _make_qr(ds, [], ann_field=None)
    with pytest.raises(ValueError, match="No annotation fields"):
        qr._resolve_annotation_field(None)


# --- export_as_coco ---


def test_export_as_coco_bbox(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="images/test.jpg", datapoint_id=0, metadata={})
    ann = IRBBoxImageAnnotation(
        filename="images/test.jpg", categories={"cat": 1.0},
        top=20.0, left=10.0, width=30.0, height=40.0,
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.DENORMALIZED,
    )
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[ann])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with patch.object(qr, "download_files"):
        result = qr.export_as_coco(download_dir=tmp_path, annotation_field="ann")

    assert result.exists()
    coco = json.loads(result.read_text())
    assert len(coco["annotations"]) == 1
    assert len(coco["images"]) == 1
    assert coco["annotations"][0]["bbox"] == [10.0, 20.0, 30.0, 40.0]


def test_export_as_coco_segmentation(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="images/test.jpg", datapoint_id=0, metadata={})
    ann = IRSegmentationImageAnnotation(
        filename="images/test.jpg", categories={"dog": 1.0},
        points=[IRSegmentationPoint(x=10, y=20), IRSegmentationPoint(x=30, y=40), IRSegmentationPoint(x=50, y=60)],
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.DENORMALIZED,
    )
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[ann])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with patch.object(qr, "download_files"):
        result = qr.export_as_coco(download_dir=tmp_path, annotation_field="ann")

    coco = json.loads(result.read_text())
    assert len(coco["annotations"]) == 1
    assert "segmentation" in coco["annotations"][0]


def test_export_as_coco_no_annotations(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="test.jpg", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with pytest.raises(RuntimeError, match="No annotations found"):
        qr.export_as_coco(download_dir=tmp_path, annotation_field="ann")


def test_export_as_coco_with_classes(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="images/test.jpg", datapoint_id=0, metadata={})
    ann = IRBBoxImageAnnotation(
        filename="images/test.jpg", categories={"cat": 1.0},
        top=20.0, left=10.0, width=30.0, height=40.0,
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.DENORMALIZED,
    )
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[ann])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with patch.object(qr, "download_files"):
        result = qr.export_as_coco(download_dir=tmp_path, annotation_field="ann", classes={1: "cat", 2: "dog"})

    coco = json.loads(result.read_text())
    cat_names = {c["name"] for c in coco["categories"]}
    assert "cat" in cat_names


# --- Helpers ---


def _make_coco_json():
    return {
        "categories": [{"id": 1, "name": "cat"}],
        "images": [{"id": 1, "width": 640, "height": 480, "file_name": "image1.jpg"}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 20, 30, 40]}],
    }


def _make_qr(ds, datapoints, ann_field=None):
    fields = []
    if ann_field:
        fields.append(MetadataSelectFieldSchema(
            asOf=int(datetime.datetime.now().timestamp()),
            autoGenerated=False, originalName=ann_field,
            multiple=False, valueType=MetadataFieldType.BLOB,
            name=ann_field, tags={ReservedTags.ANNOTATION.value},
        ))
    return QueryResult(datasource=ds, _entries=datapoints, fields=fields)
