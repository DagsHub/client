import configparser
import datetime
import json
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch, PropertyMock

import pytest
from dagshub_annotation_converter.ir.image import CoordinateStyle
from dagshub_annotation_converter.ir.video import IRVideoBBoxAnnotation

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


# --- _is_video_annotation_dict ---


def test_is_video_dict_with_int_keys():
    assert AnnotationImporter._is_video_annotation_dict({0: [], 1: []}) is True


def test_is_video_dict_with_str_keys():
    assert AnnotationImporter._is_video_annotation_dict({"file.jpg": []}) is False


def test_is_video_dict_empty():
    assert AnnotationImporter._is_video_annotation_dict({}) is False


def test_is_video_dict_non_dict():
    assert AnnotationImporter._is_video_annotation_dict([]) is False


# --- is_video_format ---


@pytest.mark.parametrize(
    "ann_type, expected",
    [
        ("yolo", False),
        ("cvat", False),
        ("coco", False),
        ("mot", True),
        ("cvat_video", True),
    ],
)
def test_is_video_format(ds, ann_type, expected, tmp_path):
    kwargs = {}
    if ann_type == "yolo":
        kwargs["yolo_type"] = "bbox"
    importer = AnnotationImporter(ds, ann_type, tmp_path / "dummy", load_from="disk", **kwargs)
    assert importer.is_video_format is expected


# --- _flatten_video_annotations ---


def test_flatten_video_annotations(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "test_video", load_from="disk")
    ann = _make_video_bbox(frame=0)
    result = importer._flatten_video_annotations({0: [ann], 5: [ann]})
    assert "test_video" in result
    assert len(result["test_video"]) == 2


def test_flatten_video_annotations_custom_name(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "test_video", load_from="disk", video_name="my_video.mp4")
    result = importer._flatten_video_annotations({0: [_make_video_bbox()]})
    assert "my_video.mp4" in result


# --- convert_to_ls_tasks for video ---


def test_convert_video_to_ls_tasks(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "video", load_from="disk")
    video_anns = {"video.mp4": [_make_video_bbox(frame=0), _make_video_bbox(frame=1)]}

    tasks = importer.convert_to_ls_tasks(video_anns)

    assert "video.mp4" in tasks
    task_json = json.loads(tasks["video.mp4"])
    assert "annotations" in task_json


# --- MOT import ---


def test_import_mot_from_dir(ds, tmp_path):
    mot_dir = tmp_path / "mot_seq"
    _create_mot_dir(mot_dir)

    importer = AnnotationImporter(ds, "mot", mot_dir, load_from="disk")
    result = importer.import_annotations()

    assert len(result) == 1
    anns = list(result.values())[0]
    assert len(anns) == 2
    assert all(isinstance(a, IRVideoBBoxAnnotation) for a in anns)


def test_import_mot_from_zip(ds, tmp_path):
    mot_dir = tmp_path / "mot_seq"
    _create_mot_dir(mot_dir)

    zip_path = tmp_path / "mot.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(mot_dir / "gt" / "gt.txt", "gt/gt.txt")
        z.write(mot_dir / "gt" / "labels.txt", "gt/labels.txt")
        z.write(mot_dir / "seqinfo.ini", "seqinfo.ini")

    importer = AnnotationImporter(ds, "mot", zip_path, load_from="disk")
    result = importer.import_annotations()

    assert len(result) == 1
    anns = list(result.values())[0]
    assert len(anns) == 2


# --- export_as_mot ---


def test_export_as_mot(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    anns = [_make_video_bbox(frame=0, track_id=1), _make_video_bbox(frame=1, track_id=1)]
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=anns)

    qr = _make_qr(ds, [dp], ann_field="ann")
    result = qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")

    assert result.exists()
    assert (result / "gt" / "gt.txt").exists()
    assert (result / "gt" / "labels.txt").exists()
    assert (result / "seqinfo.ini").exists()
    gt_lines = (result / "gt" / "gt.txt").read_text().strip().splitlines()
    assert len(gt_lines) == 2


def test_export_as_mot_no_annotations(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with pytest.raises(RuntimeError, match="No video annotations"):
        qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")


def test_export_as_mot_explicit_dimensions(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    anns = [_make_video_bbox(frame=0)]
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=anns)

    qr = _make_qr(ds, [dp], ann_field="ann")
    result = qr.export_as_mot(
        download_dir=tmp_path, annotation_field="ann", image_width=1280, image_height=720
    )

    seqinfo = (result / "seqinfo.ini").read_text()
    assert "1280" in seqinfo
    assert "720" in seqinfo


# --- Helpers ---


def _make_video_bbox(frame=0, track_id=0) -> IRVideoBBoxAnnotation:
    return IRVideoBBoxAnnotation(
        track_id=track_id, frame_number=frame,
        left=100.0, top=150.0, width=50.0, height=80.0,
        image_width=1920, image_height=1080,
        categories={"person": 1.0},
        coordinate_style=CoordinateStyle.DENORMALIZED,
    )


def _create_mot_dir(mot_dir: Path):
    gt_dir = mot_dir / "gt"
    gt_dir.mkdir(parents=True)
    (gt_dir / "gt.txt").write_text("1,1,100,150,50,80,1,1,1.0\n2,1,110,160,50,80,1,1,0.9\n")
    (gt_dir / "labels.txt").write_text("person\n")
    config = configparser.ConfigParser()
    config["Sequence"] = {
        "name": "test", "frameRate": "30", "seqLength": "100",
        "imWidth": "1920", "imHeight": "1080",
    }
    with open(mot_dir / "seqinfo.ini", "w") as f:
        config.write(f)


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
