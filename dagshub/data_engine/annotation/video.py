from collections import defaultdict
from typing import Optional, Sequence

from dagshub_annotation_converter.ir.video import (
    IRVideoBBoxFrameAnnotation,
    IRVideoAnnotationTrack,
    IRVideoSequence,
)


def build_video_sequence_from_annotations(
    annotations: Sequence[IRVideoBBoxFrameAnnotation],
    filename: Optional[str] = None,
) -> IRVideoSequence:
    # Pre-group annotations into tracks (required by new from_annotations API)
    by_track: dict[str, list[IRVideoBBoxFrameAnnotation]] = defaultdict(list)
    for ann in annotations:
        object_id = getattr(ann, "object_id", None)
        if object_id is None and ann.__pydantic_extra__ is not None:
            object_id = ann.__pydantic_extra__.get("object_id")
        if object_id is None:
            object_id = ann.imported_id
        if object_id is None:
            raise ValueError("Video annotation is missing an object identifier")
        by_track[str(object_id)].append(ann)

    tracks = [
        IRVideoAnnotationTrack.from_annotations(anns, object_id=str(tid))
        for tid, anns in by_track.items()
    ]

    sequence = IRVideoSequence.from_annotations(tracks=tracks, filename=filename)

    if filename is not None:
        for track in sequence.tracks:
            for ann in track.annotations:
                if ann.filename is None:
                    ann.filename = filename

    # resolved_* methods now cache results automatically
    sequence.resolved_video_width()
    sequence.resolved_video_height()
    sequence.resolved_sequence_length()

    return sequence
