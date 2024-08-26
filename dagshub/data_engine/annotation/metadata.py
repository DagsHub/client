from typing import TYPE_CHECKING, Optional, Sequence, Tuple, Union, Literal, Dict

from dagshub_annotation_converter.formats.label_studio.task import parse_ls_task, LabelStudioTask
from dagshub_annotation_converter.formats.yolo import import_lookup, import_yolo_result, YoloContext
from dagshub_annotation_converter.formats.yolo.categories import Categories
from dagshub_annotation_converter.ir.image import (
    IRBBoxImageAnnotation,
    CoordinateStyle,
    IRSegmentationImageAnnotation,
    IRSegmentationPoint,
    IRPoseImageAnnotation,
    IRPosePoint,
)
from dagshub_annotation_converter.ir.image.annotations.base import IRAnnotationBase, IRImageAnnotationBase

from dagshub.common.api import UserAPI
from dagshub.common.helpers import log_message

if TYPE_CHECKING:
    from dagshub.data_engine.model.datapoint import Datapoint
    import ultralytics.engine.results


class AnnotationMetaDict(dict):
    def __init__(self, annotation: "MetadataAnnotations", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.annotation = annotation

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.annotation._update_datapoint()


class MetadataAnnotations:
    """
    Class that holds metadata annotations for a datapoint.

    This class is automatically created for every datapoint,
    as long as the field is a blob field and
    :func:`has been marked as annotation \
    <dagshub.data_engine.model.metadata_field_builder.MetadataFieldBuilder.set_annotation>`


    Example of adding bounding boxes::

        dp = ds.all()[0]
        anns: MetadataAnnotations = dp["exported_annotations"]
        anns.add_image_bbox("person", 0.1, 0.1, 0.1, 0.1)
        anns.add_image_bbox("cat", 0.2, 0.2, 0.1, 0.1)
        anns.meta["some_key"] = "some_value"
        dp.save()

    You can use the ``meta`` dictionary to add additional metadata to the task, as long as it is JSON-serializable.

    All functions for adding annotations have additional arguments of ``image_width``/``image_height``.
    They are required for new datapoints, but if there are already annotations existing,
    or if there is width/height in the metadata, they can be omitted.
    """

    def __init__(
        self,
        datapoint: "Datapoint",
        field: str,
        annotations: Optional[Sequence["IRAnnotationBase"]] = None,
        meta: Optional[Dict] = None,
    ):
        self.datapoint = datapoint
        self.field = field
        self.annotations: list["IRAnnotationBase"]
        if annotations is None:
            annotations = []
        self.annotations = list(annotations)
        self.meta = AnnotationMetaDict(self, meta or {})

    @staticmethod
    def from_ls_task(datapoint: "Datapoint", field: str, ls_task: bytes) -> "MetadataAnnotations":
        parsed_ls_task = parse_ls_task(ls_task)
        annotations = parsed_ls_task.to_ir_annotations(filename=datapoint.path)

        return MetadataAnnotations(datapoint=datapoint, field=field, annotations=annotations, meta=parsed_ls_task.meta)

    def to_ls_task(self) -> Optional[bytes]:
        """
        Convert the annotations into a Label Studio task (this is what's stored in the Data Engine backend).
        """
        if len(self.annotations) == 0:
            return None
        task = LabelStudioTask(
            user_id=UserAPI.get_current_user(self.datapoint.datasource.source.repoApi.host).user_id,
        )
        task.data["image"] = self.datapoint.download_url
        # TODO: need to filter out non-image annotations here maybe?
        task.add_ir_annotations(self.annotations)
        task.meta.update(self.meta)
        return task.model_dump_json().encode("utf-8")

    def __repr__(self):
        return f"Annotations:\n\t{self.annotations}"

    def get_image_dimensions(self, image_width: Optional[int], image_height: Optional[int]) -> Tuple[int, int]:
        """
        Get dimensions of the image.
        If not provided, tries to get them from the existing annotations or the datapoint metadata.

        :meta private:
        """
        if image_width is not None and image_height is not None:
            return image_width, image_height

        for ann in self.annotations:
            if isinstance(ann, IRImageAnnotationBase):
                return ann.image_width, ann.image_height

        if "width" not in self.datapoint.metadata:
            raise ValueError('Image width not provided, and a "width" field was not found in the datapoint')
        if "height" not in self.datapoint.metadata:
            raise ValueError('Image height not provided, and a "height" field was not found in the datapoint')
        return self.datapoint["width"], self.datapoint["height"]

    def _update_datapoint(self):
        """
        Fire this method on every update to save annotations in the datapoint
        """
        self.datapoint[self.field] = self

    def add_image_bbox(
        self,
        category: str,
        top: float,
        left: float,
        width: float,
        height: float,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ):
        """
        Adds a bounding box annotation.
        Values need to be normalized from 0 to 1

        Args:
            category: Annotation category
            top: Top coordinate of the bounding box
            left: Left coordinate of the bounding box
            width: Width of the bounding box
            height: Height of the bounding box
            image_width: Width of the image. If not supplied, tries to get it from the `width` field in datapoint
            image_height: Height of the image. If not supplied, tries to get it from the `height` field in datapoint
        """
        image_width, image_height = self.get_image_dimensions(image_width, image_height)
        self.annotations.append(
            IRBBoxImageAnnotation(
                filename=self.datapoint.path,
                categories={category: 1.0},
                top=top,
                left=left,
                width=width,
                height=height,
                image_width=image_width,
                image_height=image_height,
                coordinate_style=CoordinateStyle.NORMALIZED,
            )
        )
        self._update_datapoint()

    def add_image_segmentation(
        self,
        category: str,
        points: Sequence[Tuple[float, float]],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ):
        """
        Add a segmentation annotation.
        Points need to be a list of tuples of 2 (x, y) values, normalized from 0 to 1.
        Example of points: ``[(0.1, 0.1), (0.3, 0.3), (0.1, 0.6)]``


        Args:
            category: Annotation category
            points: List of points of the segmentation
            image_width: Width of the image. If not supplied, tries to get it from the `width` field in datapoint
            image_height: Height of the image. If not supplied, tries to get it from the `height` field in datapoint
        """
        image_width, image_height = self.get_image_dimensions(image_width, image_height)
        self.annotations.append(
            IRSegmentationImageAnnotation(
                filename=self.datapoint.path,
                categories={category: 1.0},
                points=[IRSegmentationPoint(x=x, y=y) for x, y in points],
                image_width=image_width,
                image_height=image_height,
                coordinate_style=CoordinateStyle.NORMALIZED,
            )
        )
        self._update_datapoint()

    def add_image_pose(
        self,
        category: str,
        points: Union[Sequence[Tuple[float, float]], Sequence[Tuple[float, float, Optional[bool]]]],
        bbox_left: Optional[float] = None,
        bbox_top: Optional[float] = None,
        bbox_width: Optional[float] = None,
        bbox_height: Optional[float] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ):
        """
        Adds a new pose annotation

        ``bbox_...`` arguments define the bounding box of the pose. If any of the parameters is not defined,
        the bounding box is instead created from the points.

        Points need to be a list of tuples of ``(x, y)`` or ``(x, y, visible)`` values, normalized from 0 to 1.

        Args:
            category: Annotation category
            points: List of points of the pose
            bbox_left: Left coordinate of the bounding box
            bbox_top: Top coordinate of the bounding box
            bbox_width: Width of the bounding box
            bbox_height: Height of the bounding box
            image_width: Width of the image. If not supplied, tries to get it from the `width` field in datapoint
            image_height: Height of the image. If not supplied, tries to get it from the `height` field in datapoint
        """

        image_width, image_height = self.get_image_dimensions(image_width, image_height)

        pose_points: list[IRPosePoint] = []
        for p in points:
            if len(p) == 2:
                pose_points.append(IRPosePoint(x=p[0], y=p[1]))
            else:
                pose_points.append(IRPosePoint(x=p[0], y=p[1], visible=p[2]))

        ann = IRPoseImageAnnotation.from_points(
            filename=self.datapoint.path,
            categories={category: 1.0},
            points=pose_points,
            image_width=image_width,
            image_height=image_height,
            coordinate_style=CoordinateStyle.NORMALIZED,
        )

        if bbox_left is not None and bbox_top is not None and bbox_width is not None and bbox_height is not None:
            ann.left = bbox_left
            ann.top = bbox_top
            ann.width = bbox_width
            ann.height = bbox_height

        self.annotations.append(ann)
        self._update_datapoint()

    def add_yolo_annotation(
        self,
        annotation_type: Literal["bbox", "segmentation", "pose"],
        annotation: Union[str, "ultralytics.engine.results.Results"],
        categories: Optional[Dict[int, str]] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        pose_keypoint_dim: Optional[int] = None,
    ):
        """
        Add a YOLO annotation from string or from a result of prediction with a YOLO model.

        This could be either a string of an annotations from a YOLO file, or a result of evaluating a YOLO model.
        Args:

        """
        annotations: list[IRAnnotationBase] = []
        if isinstance(annotation, str):
            if categories is None:
                raise ValueError("`categories` dictionary is required when importing annotations from a string")
            image_width, image_height = self.get_image_dimensions(image_width, image_height)
            yolo_context = self._generate_yolo_context(annotation_type, categories)
            if annotation_type == "pose":
                if pose_keypoint_dim is None:
                    raise ValueError("`pose_keypoint_dim` is required when importing pose annotations")
                yolo_context.keypoint_dim = pose_keypoint_dim
            parse_fn = import_lookup[annotation_type]
            for ann in annotation.split("\n"):
                new_ann = parse_fn(ann, yolo_context, image_width, image_height, None)
                new_ann.filename = self.datapoint.path
                annotations.append(new_ann)
        else:
            new_anns = import_yolo_result(annotation_type, annotation)
            for new_ann in new_anns:
                new_ann.filename = self.datapoint.path
            annotations.extend(new_anns)
        self.annotations.extend(annotations)
        log_message(f"Added {len(annotations)} YOLO annotation(s) to datapoint {self.datapoint.path}")
        self._update_datapoint()

    @staticmethod
    def _generate_yolo_context(annotation_type, categories: Dict[int, str]) -> YoloContext:
        cats = Categories()
        for cat_id, cat_name in categories.items():
            cats.add(cat_name, cat_id)
        return YoloContext(annotation_type=annotation_type, categories=cats)
