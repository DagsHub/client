import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagshub.data_engine.client.models import Datapoint
    import fiftyone as fo

logger = logging.getLogger(__name__)


def add_voxel_annotations(sample: "fo.Sample", datapoint: "Datapoint", *annotation_fields: str):
    """
    Adds annotation to the voxel sample.

    Args:
        sample (fo.Sample): FiftyOne sample to add the annotations to
        datapoint (Datapoint): Data Engine datapoint to get metadata from
        annotation_fields(str): JSON blobs of voxel annotations that are added to sample.
    """
    from fiftyone import Label

    for field in annotation_fields:
        annotation_val = datapoint.get_blob(field)
        label = Label.from_json(annotation_val.decode())
        sample.add_labels(label, label_field=field)


def add_ls_annotations(sample: "fo.Sample", datapoint: "Datapoint", *annotation_fields: str):
    """
    Adds LabelStudio annotation to the voxel sample.

    Args:
        sample: FiftyOne sample to add the annotations to
        datapoint: Data Engine datapoint to get metadata from
        annotation_fields: fields from which to get annotations
    """
    from fiftyone.utils.labelstudio import import_label_studio_annotation
    from fiftyone import (
        Detections,
        Detection,
        Classification,
        Classifications,
        Keypoint,
        Keypoints,
        Polylines,
        Polyline,
    )

    for field in annotation_fields:
        annotations = datapoint.metadata.get(field)
        if type(annotations) is not bytes:
            return
        ann_dict = json.loads(annotations.decode())
        for ann in ann_dict.get("annotations", {}):
            if "result" not in ann:
                continue
            annotations = []
            for res in ann["result"]:
                try:
                    converted = import_label_studio_annotation(res)
                    if type(converted) is tuple:
                        converted = converted[1]
                    annotations.append(converted)
                except Exception:
                    logger.warning(f"Couldn't convert LS annotation {ann} to voxel annotation")

            if len(annotations) == 0:
                continue
            # Group the annotations of a similar type together
            # For now assuming there's no mixing and matching
            ann_type = type(annotations[0])
            if ann_type is Detection:
                labels = Detections()
                for a in annotations:
                    labels.detections.append(a)
                labels = [labels]
            elif ann_type is Classification:
                labels = Classifications()
                for a in annotations:
                    labels.classifications.append(a)
                labels = [labels]
            elif ann_type is Keypoint:
                labels = Keypoints()
                for a in annotations:
                    labels.keypoints.append(a)
                labels = [labels]
            elif ann_type is Polyline:
                labels = Polylines()
                for a in annotations:
                    labels.polylines.append(a)
                labels = [labels]
            else:
                labels = annotations

            for label in labels:
                sample.add_labels(label, label_field=field)
