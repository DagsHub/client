from typing import Optional, Sequence

from dagshub_annotation_converter.ir.video import IRVideoBBoxFrameAnnotation, IRVideoSequence


def build_video_sequence_from_annotations(
    annotations: Sequence[IRVideoBBoxFrameAnnotation],
    filename: Optional[str] = None,
) -> IRVideoSequence:
    sequence = IRVideoSequence.from_annotations(annotations, filename=filename)

    resolved_width = sequence.resolved_video_width()
    if sequence.video_width is None and resolved_width is not None:
        sequence.video_width = resolved_width

    resolved_height = sequence.resolved_video_height()
    if sequence.video_height is None and resolved_height is not None:
        sequence.video_height = resolved_height

    resolved_length = sequence.resolved_sequence_length()
    if sequence.sequence_length is None and resolved_length is not None:
        sequence.sequence_length = resolved_length

    return sequence
