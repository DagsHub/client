import datetime
from pathlib import PurePosixPath
from unittest.mock import patch, PropertyMock

import pytest
from dagshub_annotation_converter.converters.cvat import export_cvat_video_to_xml_string
from dagshub_annotation_converter.ir.image import IRBBoxImageAnnotation, CoordinateStyle
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


# --- import ---


def test_import_cvat_video(ds, tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_bytes(_make_cvat_video_xml())

    importer = AnnotationImporter(ds, "cvat_video", xml_file, load_from="disk")
    result = importer.import_annotations()

    assert len(result) == 1
    anns = list(result.values())[0]
    assert len(anns) == 2
    assert all(isinstance(a, IRVideoBBoxAnnotation) for a in anns)


# --- _get_all_video_annotations ---


def test_get_all_video_filters(ds):
    image_ann = IRBBoxImageAnnotation(
        filename="test.jpg", categories={"cat": 1.0},
        top=0.1, left=0.1, width=0.2, height=0.2,
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.NORMALIZED,
    )
    video_ann = _make_video_bbox()

    dp = Datapoint(datasource=ds, path="dp_0", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(
        datapoint=dp, field="ann", annotations=[image_ann, video_ann]
    )

    qr = _make_qr(ds, [dp], ann_field="ann")
    result = qr._get_all_video_annotations("ann")
    assert len(result) == 1
    assert isinstance(result[0], IRVideoBBoxAnnotation)


def test_get_all_video_empty(ds):
    dp = Datapoint(datasource=ds, path="dp_0", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[])

    qr = _make_qr(ds, [dp], ann_field="ann")
    assert qr._get_all_video_annotations("ann") == []


def test_get_all_video_aggregates_across_datapoints(ds):
    dps = []
    for i in range(3):
        dp = Datapoint(datasource=ds, path=f"dp_{i}", datapoint_id=i, metadata={})
        dp.metadata["ann"] = MetadataAnnotations(
            datapoint=dp, field="ann", annotations=[_make_video_bbox(frame=i)]
        )
        dps.append(dp)

    qr = _make_qr(ds, dps, ann_field="ann")
    assert len(qr._get_all_video_annotations("ann")) == 3


# --- export_as_cvat_video ---


def test_export_cvat_video_xml(ds, tmp_path):
    qr, _ = _make_video_qr(ds)
    result = qr.export_as_cvat_video(download_dir=tmp_path, annotation_field="ann")

    assert result.exists()
    content = result.read_text()
    assert "<track" in content
    assert "<box" in content


def test_export_cvat_video_no_annotations_raises(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with pytest.raises(RuntimeError, match="No video annotations"):
        qr.export_as_cvat_video(download_dir=tmp_path, annotation_field="ann")


def test_export_cvat_video_custom_name(ds, tmp_path):
    qr, _ = _make_video_qr(ds)
    result = qr.export_as_cvat_video(
        download_dir=tmp_path, annotation_field="ann", video_name="my_clip.avi"
    )

    content = result.read_text()
    assert "my_clip.avi" in content


def test_export_cvat_video_image_only_raises(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    image_ann = IRBBoxImageAnnotation(
        filename="test.jpg", categories={"cat": 1.0},
        top=0.1, left=0.1, width=0.2, height=0.2,
        image_width=640, image_height=480,
        coordinate_style=CoordinateStyle.NORMALIZED,
    )
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[image_ann])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with pytest.raises(RuntimeError, match="No video annotations"):
        qr.export_as_cvat_video(download_dir=tmp_path, annotation_field="ann")


def test_export_cvat_video_multiple_datapoints(ds, tmp_path):
    dps = []
    for i in range(2):
        dp = Datapoint(datasource=ds, path=f"video_{i}.mp4", datapoint_id=i, metadata={})
        dp.metadata["ann"] = MetadataAnnotations(
            datapoint=dp, field="ann",
            annotations=[_make_video_bbox(frame=i, track_id=i)],
        )
        dps.append(dp)

    qr = _make_qr(ds, dps, ann_field="ann")
    result = qr.export_as_cvat_video(download_dir=tmp_path, annotation_field="ann")

    content = result.read_text()
    assert content.count("<box") >= 2


# --- helpers ---


def _make_video_bbox(frame=0, track_id=0) -> IRVideoBBoxAnnotation:
    return IRVideoBBoxAnnotation(
        track_id=track_id, frame_number=frame,
        left=100.0, top=150.0, width=50.0, height=80.0,
        image_width=1920, image_height=1080,
        categories={"person": 1.0},
        coordinate_style=CoordinateStyle.DENORMALIZED,
    )


def _make_cvat_video_xml() -> bytes:
    anns = [_make_video_bbox(frame=0, track_id=0), _make_video_bbox(frame=5, track_id=0)]
    return export_cvat_video_to_xml_string(anns)


def _make_video_qr(ds):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    anns = [_make_video_bbox(frame=0, track_id=0), _make_video_bbox(frame=5, track_id=0)]
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=anns)
    qr = _make_qr(ds, [dp], ann_field="ann")
    return qr, dp


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
