from typing import TYPE_CHECKING, Optional, Sequence, Tuple, Union, Literal

from dagshub_annotation_converter.formats.label_studio.task import parse_ls_task, LabelStudioTask
from dagshub_annotation_converter.formats.yolo import YoloContext, import_lookup, import_yolo_result
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


class Annotations:
    def __init__(
        self,
        datapoint: "Datapoint",
        annotations: Optional[Sequence["IRAnnotationBase"]] = None,
        original_ls_task: Optional["LabelStudioTask"] = None,
    ):
        self.datapoint = datapoint
        self.annotations: list["IRAnnotationBase"]
        self.original_ls_task = original_ls_task
        if annotations is None:
            annotations = []
        self.annotations = list(annotations)

    @staticmethod
    def from_ls_task(datapoint: "Datapoint", ls_task: bytes) -> "Annotations":
        parsed_ls_task = parse_ls_task(ls_task)
        annotations = parsed_ls_task.to_ir_annotations(filename=datapoint.path)

        return Annotations(datapoint=datapoint, annotations=annotations, original_ls_task=parsed_ls_task)

    def to_ls_task(self) -> bytes:
        task = LabelStudioTask(
            user_id=UserAPI.get_current_user(self.datapoint.datasource.source.repoApi.host).user_id,
        )
        task.data["image"] = self.datapoint.download_url
        # TODO: need to filter out non-image annotations here maybe?
        task.add_ir_annotations(self.annotations)
        return task.model_dump_json().encode("utf-8")

    def has_changed(self) -> bool:
        """
        Checks that the annotations have changed from the original LS task.
        NOTE: This deserializes the LS task, so it's not a super cheap operation, use sparingly.
        """
        if self.original_ls_task is None:
            if len(self.annotations) == 0:
                return False
            return True

        reparsed = self.original_ls_task.to_ir_annotations(filename=self.datapoint.path)
        return reparsed != self.annotations

    def __repr__(self):
        return f"Annotations:\n\t{self.annotations}"

    def get_image_dimensions(self, image_width: Optional[int], image_height: Optional[int]) -> Tuple[int, int]:
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
        Example of points: [(0.1, 0.1), (0.3, 0.3), (0.1, 0.6)]


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

        Points need to be a list of tuples of (x, y) or (x, y, visible) values, normalized from 0 to 1.
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

    def add_yolo_annotation(
        self,
        annotation_type: Literal["bbox", "segmentation", "pose"],
        annotation: Union[str, "ultralytics.engine.results.Results"],
        yolo_context: Optional["YoloContext"] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ):
        annotations: list[IRAnnotationBase] = []
        if isinstance(annotation, str):
            if yolo_context is None:
                raise ValueError("YoloContext is required when importing annotations from a string")
            image_width, image_height = self.get_image_dimensions(image_width, image_height)
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
