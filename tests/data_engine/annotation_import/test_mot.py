import configparser
import datetime
import json
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch, PropertyMock

import pytest
from dagshub_annotation_converter.ir.image import CoordinateStyle
from dagshub_annotation_converter.ir.video import IRVideoBBoxFrameAnnotation

from dagshub.data_engine.annotation.importer import AnnotationImporter, AnnotationsNotFoundError
from dagshub.data_engine.annotation.metadata import MetadataAnnotations
from dagshub.data_engine.annotation.video import build_video_sequence_from_annotations
from dagshub.data_engine.client.models import MetadataSelectFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType, ReservedTags
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.query_result import QueryResult


@pytest.fixture(autouse=True)
def mock_source_prefix(ds):
    with patch.object(type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath()):
        yield


# --- _is_video_annotation ---


def test_is_video_dict_int_keys():
    assert AnnotationImporter._is_video_annotation({0: [], 1: []}) is True


def test_is_video_dict_str_keys():
    assert AnnotationImporter._is_video_annotation({"file.jpg": []}) is False


def test_is_video_dict_empty():
    assert AnnotationImporter._is_video_annotation({}) is False


def test_is_video_dict_non_dict():
    assert AnnotationImporter._is_video_annotation([]) is False


def test_is_video_dict_mixed_first_int():
    assert AnnotationImporter._is_video_annotation({0: [], "a": []}) is True


def test_is_video_sequence():
    seq = build_video_sequence_from_annotations([_make_video_bbox()])
    assert AnnotationImporter._is_video_annotation(seq) is True


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


def test_flatten_merges_frames(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "test_video", load_from="disk")
    result = importer._flatten_video_annotations({
        0: [_make_video_bbox(frame=0)],
        5: [_make_video_bbox(frame=5)],
    })
    assert "test_video" in result
    assert len(result["test_video"]) == 2


def test_flatten_defaults_to_file_stem(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "my_sequence", load_from="disk")
    result = importer._flatten_video_annotations({0: [_make_video_bbox()]})
    assert "my_sequence" in result


def test_flatten_video_name_override(ds, tmp_path):
    importer = AnnotationImporter(
        ds, "mot", tmp_path / "test_video", load_from="disk", video_name="custom.mp4"
    )
    result = importer._flatten_video_annotations({0: [_make_video_bbox()]})
    assert "custom.mp4" in result


def test_flatten_sequence(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "test_video", load_from="disk")
    sequence = build_video_sequence_from_annotations([_make_video_bbox(frame=0), _make_video_bbox(frame=5)])
    result = importer._flatten_video_annotations(sequence)

    assert "test_video" in result
    assert len(result["test_video"]) == 2


def test_flatten_sequence_preserves_sequence_filename(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "dataset", load_from="disk")
    sequence = build_video_sequence_from_annotations(
        [_make_video_bbox(frame=0), _make_video_bbox(frame=5)],
        filename="nested/videos/video.mp4",
    )

    result = importer._flatten_video_annotations(sequence)

    assert "nested/videos/video.mp4" in result


def test_flatten_mot_fs_preserves_relative_video_path(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "dataset", load_from="disk")
    sequence = build_video_sequence_from_annotations(
        [_make_video_bbox(frame=0), _make_video_bbox(frame=5)],
        filename="nested/video.mp4",
    )

    result = importer._flatten_mot_fs_annotations({Path("nested/video.mp4"): (sequence, object())})

    assert "nested/video.mp4" in result


def test_build_video_sequence_sets_top_level_dimensions():
    anns = [
        IRVideoBBoxFrameAnnotation(
            object_id=0,
            frame_number=0,
            left=100.0,
            top=150.0,
            width=50.0,
            height=80.0,
            video_width=1920,
            video_height=1080,
            categories={"person": 1.0},
            coordinate_style=CoordinateStyle.DENORMALIZED,
        )
    ]

    sequence = build_video_sequence_from_annotations(anns, filename="video.mp4")

    assert sequence.video_width == 1920
    assert sequence.video_height == 1080


def test_video_export_layout_uses_datasource_prefix(ds):
    qr, _ = _make_video_qr(ds)
    with patch.object(
        type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath("my_ds_path")
    ):
        video_dir, labels_dir, dataset_root = qr._get_media_export_layout(Path("export"), "videos")

    assert video_dir == Path("export") / "data" / "my_ds_path" / "videos"
    assert labels_dir == Path("export") / "data" / "my_ds_path" / "labels"
    assert dataset_root == Path("export") / "data" / "my_ds_path"


def test_video_export_layout_reuses_existing_videos_suffix(ds):
    qr, _ = _make_video_qr(ds)
    with patch.object(
        type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath("my_ds_path/videos")
    ):
        video_dir, labels_dir, dataset_root = qr._get_media_export_layout(Path("export"), "videos")

    assert video_dir == Path("export") / "data" / "my_ds_path" / "videos"
    assert labels_dir == Path("export") / "data" / "my_ds_path" / "labels"
    assert dataset_root == Path("export") / "data" / "my_ds_path"


def test_video_export_layout_strips_leading_data_prefix(ds):
    qr, _ = _make_video_qr(ds)
    with patch.object(
        type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath("data/videos")
    ):
        video_dir, labels_dir, dataset_root = qr._get_media_export_layout(Path("export"), "videos")

    assert video_dir == Path("export") / "data" / "videos"
    assert labels_dir == Path("export") / "data" / "labels"
    assert dataset_root == Path("export") / "data"


# --- import ---


def test_import_mot_from_dir(ds, tmp_path):
    mot_dir = tmp_path / "mot_seq"
    _create_mot_dir(mot_dir)

    importer = AnnotationImporter(ds, "mot", mot_dir, load_from="disk")
    result = importer.import_annotations()

    assert len(result) == 1
    anns = list(result.values())[0]
    assert len(anns) == 2
    assert all(isinstance(a, IRVideoBBoxFrameAnnotation) for a in anns)


def test_import_mot_from_zip(ds, tmp_path):
    mot_dir = tmp_path / "mot_seq"
    _create_mot_dir(mot_dir)
    zip_path = _zip_mot_dir(tmp_path, mot_dir)

    importer = AnnotationImporter(ds, "mot", zip_path, load_from="disk")
    result = importer.import_annotations()

    assert len(result) == 1
    assert len(list(result.values())[0]) == 2


def test_import_mot_from_fs_passes_dimensions(ds, tmp_path, monkeypatch):
    # Create the labels/ subdir so the importer takes the load_mot_from_fs path
    (tmp_path / "labels").mkdir()
    captured = {}

    def _mock_load_mot_from_fs(import_dir, image_width=None, image_height=None, **kwargs):
        captured["import_dir"] = import_dir
        captured["image_width"] = image_width
        captured["image_height"] = image_height
        return {Path("seq_a"): ({0: [_make_video_bbox(frame=0)]}, object())}

    monkeypatch.setattr("dagshub.data_engine.annotation.importer.load_mot_from_fs", _mock_load_mot_from_fs)

    with patch.object(
        type(ds.source), "source_prefix", new_callable=PropertyMock, return_value=PurePosixPath("data/videos")
    ):
        importer = AnnotationImporter(
            ds,
            "mot",
            tmp_path,
            load_from="disk",
            image_width=1280,
            image_height=720,
        )
        result = importer.import_annotations()

    assert captured["image_width"] == 1280
    assert captured["image_height"] == 720
    assert "seq_a" in result


def test_import_mot_nonexistent_raises(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "missing", load_from="disk")
    with pytest.raises(AnnotationsNotFoundError):
        importer.import_annotations()


# --- convert_to_ls_tasks ---


def test_convert_video_to_ls_tasks(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "video", load_from="disk")
    video_anns = {"video.mp4": [_make_video_bbox(frame=0), _make_video_bbox(frame=1)]}
    tasks = importer.convert_to_ls_tasks(video_anns)

    assert "video.mp4" in tasks
    task_json = json.loads(tasks["video.mp4"])
    assert "annotations" in task_json


def test_convert_video_empty_skipped(ds, tmp_path):
    importer = AnnotationImporter(ds, "mot", tmp_path / "video", load_from="disk")
    tasks = importer.convert_to_ls_tasks({"video.mp4": []})
    assert "video.mp4" not in tasks


# --- export_as_mot ---


def test_export_mot_directory_structure(ds, tmp_path, monkeypatch):
    qr, _ = _make_video_qr(ds)
    captured = {}

    def _mock_download_files(self, target_dir, *args, **kwargs):
        captured["download_dir"] = target_dir
        captured["keep_source_prefix"] = kwargs.get("keep_source_prefix", True)
        (target_dir / "video.mp4").parent.mkdir(parents=True, exist_ok=True)
        (target_dir / "video.mp4").write_bytes(b"fake")
        return target_dir

    def _mock_export_mot_to_dir(video_annotations, context, output_dir, video_file=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "gt").mkdir(parents=True, exist_ok=True)
        (output_dir / "gt" / "gt.txt").write_text("")
        (output_dir / "gt" / "labels.txt").write_text("person\n")
        config = configparser.ConfigParser()
        config["Sequence"] = {"imWidth": "1920", "imHeight": "1080"}
        with open(output_dir / "seqinfo.ini", "w") as f:
            config.write(f)
        return output_dir

    monkeypatch.setattr(QueryResult, "download_files", _mock_download_files)
    monkeypatch.setattr(
        "dagshub.data_engine.model.query_result.export_mot_to_dir",
        _mock_export_mot_to_dir,
    )
    result = qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")

    assert result.exists()
    assert result == tmp_path / "data" / "labels" / "video"
    assert captured["download_dir"] == tmp_path / "data" / "videos"
    assert captured["keep_source_prefix"] is False
    assert (result / "gt" / "gt.txt").exists()
    assert (result / "gt" / "labels.txt").exists()
    assert (result / "seqinfo.ini").exists()


def test_export_mot_explicit_dimensions(ds, tmp_path, monkeypatch):
    qr, _ = _make_video_qr(ds)
    captured = {}

    def _mock_download_files(self, target_dir, *args, **kwargs):
        captured["download_dir"] = target_dir
        (target_dir / "video.mp4").parent.mkdir(parents=True, exist_ok=True)
        (target_dir / "video.mp4").write_bytes(b"fake")
        return target_dir

    def _mock_export_mot_to_dir(video_annotations, context, output_dir, video_file=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config["Sequence"] = {
            "imWidth": str(context.video_width),
            "imHeight": str(context.video_height),
        }
        with open(output_dir / "seqinfo.ini", "w") as f:
            config.write(f)
        (output_dir / "gt").mkdir(parents=True, exist_ok=True)
        (output_dir / "gt" / "gt.txt").write_text("")
        (output_dir / "gt" / "labels.txt").write_text("person\n")
        return output_dir

    monkeypatch.setattr(QueryResult, "download_files", _mock_download_files)
    monkeypatch.setattr(
        "dagshub.data_engine.model.query_result.export_mot_to_dir",
        _mock_export_mot_to_dir,
    )
    result = qr.export_as_mot(
        download_dir=tmp_path, annotation_field="ann", image_width=1280, image_height=720
    )

    seqinfo = (result / "seqinfo.ini").read_text()
    assert captured["download_dir"] == tmp_path / "data" / "videos"
    assert "1280" in seqinfo
    assert "720" in seqinfo


def test_export_mot_no_annotations_raises(ds, tmp_path):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[])

    qr = _make_qr(ds, [dp], ann_field="ann")
    with pytest.raises(RuntimeError, match="No video annotations"):
        qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")


def test_export_mot_multiple_videos(ds, tmp_path, monkeypatch):
    dps = []
    for i in range(2):
        dp = Datapoint(datasource=ds, path=f"video_{i}.mp4", datapoint_id=i, metadata={})
        ann = _make_video_bbox(frame=i, object_id=i)
        ann.filename = dp.path
        dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=[ann])
        dps.append(dp)

    captured = {}

    def _mock_download_files(self, target_dir, *args, **kwargs):
        captured["download_dir"] = target_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        for i in range(2):
            (target_dir / f"video_{i}.mp4").write_bytes(b"fake")
        return target_dir

    def _mock_export_mot_sequences_to_dirs(video_annotations, context, output_dir):
        captured["output_dir"] = output_dir
        for i in range(2):
            seq_dir = output_dir / "labels" / f"video_{i}"
            seq_dir.mkdir(parents=True, exist_ok=True)
            (seq_dir / "gt").mkdir(parents=True, exist_ok=True)
            (seq_dir / "gt" / "gt.txt").write_text("")
            (seq_dir / "gt" / "labels.txt").write_text("person\n")
        return output_dir / "labels"

    monkeypatch.setattr(QueryResult, "download_files", _mock_download_files)
    monkeypatch.setattr(
        "dagshub.data_engine.model.query_result.export_mot_sequences_to_dirs",
        _mock_export_mot_sequences_to_dirs,
    )
    qr = _make_qr(ds, dps, ann_field="ann")
    result = qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")

    assert result == tmp_path / "data"
    assert captured["download_dir"] == tmp_path / "data" / "videos"
    assert captured["output_dir"] == tmp_path / "data"
    assert (result / "labels" / "video_0" / "gt" / "gt.txt").exists()
    assert (result / "labels" / "video_1" / "gt" / "gt.txt").exists()


def test_export_mot_passes_video_file_when_dimensions_missing(ds, tmp_path, monkeypatch):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    anns = [_make_video_bbox(frame=0, object_id=1), _make_video_bbox(frame=1, object_id=1)]
    for ann in anns:
        ann.video_width = 0
        ann.video_height = 0
        ann.filename = "video.mp4"
    dp.metadata["ann"] = MetadataAnnotations(datapoint=dp, field="ann", annotations=anns)
    qr = _make_qr(ds, [dp], ann_field="ann")

    captured = {}

    def _mock_download_files(self, target_dir, *args, **kwargs):
        video_path = target_dir / "video.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"video")
        return target_dir

    def _mock_export_mot_to_dir(video_annotations, context, output_dir, video_file=None):
        captured["video_file"] = str(video_file) if video_file is not None else None
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    monkeypatch.setattr(QueryResult, "download_files", _mock_download_files)
    monkeypatch.setattr("dagshub.data_engine.model.query_result.export_mot_to_dir", _mock_export_mot_to_dir)

    qr.export_as_mot(download_dir=tmp_path, annotation_field="ann")

    assert captured["video_file"] is not None
    assert "data/videos" in captured["video_file"]
    assert captured["video_file"].endswith("video.mp4")


# --- helpers ---


def _make_video_bbox(frame=0, object_id=0) -> IRVideoBBoxFrameAnnotation:
    return IRVideoBBoxFrameAnnotation(
        object_id=object_id, frame_number=frame,
        left=100.0, top=150.0, width=50.0, height=80.0,
        video_width=1920, video_height=1080,
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


def _zip_mot_dir(tmp_path: Path, mot_dir: Path) -> Path:
    zip_path = tmp_path / "mot.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(mot_dir / "gt" / "gt.txt", "gt/gt.txt")
        z.write(mot_dir / "gt" / "labels.txt", "gt/labels.txt")
        z.write(mot_dir / "seqinfo.ini", "seqinfo.ini")
    return zip_path


def _make_video_qr(ds):
    dp = Datapoint(datasource=ds, path="video.mp4", datapoint_id=0, metadata={})
    anns = [_make_video_bbox(frame=0, object_id=1), _make_video_bbox(frame=1, object_id=1)]
    for ann in anns:
        ann.filename = "video.mp4"
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
