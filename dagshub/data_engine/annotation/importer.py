from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath, PurePath
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Dict, Iterable, Literal, Optional, Union, Sequence, Mapping, Callable, List, Tuple

from dagshub_annotation_converter.converters.coco import load_coco_from_file
from dagshub_annotation_converter.converters.cvat import (
    CVATAnnotations,
    load_cvat_from_fs,
    load_cvat_from_zip,
    load_cvat_from_xml_file,
)
from dagshub_annotation_converter.converters.mot import load_mot_from_dir, load_mot_from_fs, load_mot_from_zip
from dagshub_annotation_converter.formats.mot.context import MOTContext
from dagshub_annotation_converter.converters.yolo import load_yolo_from_fs
from dagshub_annotation_converter.converters.label_studio_video import video_ir_to_ls_video_task
from dagshub_annotation_converter.formats.label_studio.task import LabelStudioTask
from dagshub_annotation_converter.formats.yolo import YoloContext
from dagshub_annotation_converter.ir.base import IRTaskAnnotation
from dagshub_annotation_converter.ir.image.annotations.base import IRAnnotationBase
from dagshub_annotation_converter.ir.video import IRVideoAnnotationTrack, IRVideoBBoxFrameAnnotation, IRVideoSequence

from dagshub.common.api import UserAPI
from dagshub.common.api.repo import PathNotFoundError
from dagshub.common.helpers import log_message
from dagshub.data_engine.annotation.video import build_video_sequence_from_annotations

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

AnnotationType = Literal["yolo", "cvat", "coco", "mot", "cvat_video"]
AnnotationLocation = Literal["repo", "disk"]


class AnnotationsNotFoundError(Exception):
    def __init__(self, path):
        super().__init__(f'Annotations not found at path "{path}" in neither disk or repository.')


class CannotRemapPathError(Exception):
    def __init__(self, a_path, b_path):
        super().__init__(f"Cannot map from path {a_path} to path {b_path}")


class AnnotationImporter:
    """
    Class for importing annotations into a datasource from different formats.
    """

    def __init__(
        self,
        ds: "Datasource",
        annotations_type: AnnotationType,
        annotations_file: Union[str, Path],
        load_from: Optional[AnnotationLocation] = None,
        **kwargs,
    ):
        self.ds = ds.__deepcopy__()
        self.ds.clear_query()
        self.annotations_type = annotations_type
        self.annotations_file = Path(annotations_file)
        self.load_from = load_from if load_from is not None else self.determine_load_location(ds, annotations_file)
        self.additional_args = kwargs

        if self.annotations_type == "yolo":
            if "yolo_type" not in kwargs:
                raise ValueError(
                    "YOLO type must be provided in the additional arguments. "
                    'Add `yolo_type="bbox"|"segmentation"|pose"` to the arguments.'
                )

    @property
    def is_video_format(self) -> bool:
        return self.annotations_type in ("mot", "cvat_video")

    def import_annotations(self) -> Mapping[str, Sequence[IRTaskAnnotation]]:
        # Double check that the annotation file exists
        if self.load_from == "disk":
            if not self.annotations_file.exists():
                raise AnnotationsNotFoundError(self.annotations_file)
        elif self.load_from == "repo":
            try:
                self.ds.source.repoApi.list_path(self.annotations_file.as_posix())
            except PathNotFoundError:
                raise AnnotationsNotFoundError(self.annotations_file)

        annotations_file = self.annotations_file

        with TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            if self.load_from == "repo":
                self.download_annotations(tmp_dir_path)
                annotations_file = tmp_dir_path / annotations_file.name

            # Convert annotations
            log_message("Loading annotations...")
            annotation_dict: Mapping[str, Sequence[IRTaskAnnotation]]
            if self.annotations_type == "yolo":
                annotation_dict, _ = load_yolo_from_fs(
                    annotation_type=self.additional_args["yolo_type"], meta_file=annotations_file
                )
            elif self.annotations_type == "cvat":
                if annotations_file.is_dir():
                    annotation_dict = self._key_cvat_fs_annotations_by_filename(load_cvat_from_fs(annotations_file))
                else:
                    result = load_cvat_from_zip(annotations_file)
                    if self._determine_cvat_annotation(result) == "video":
                        annotation_dict = self._key_video_annotations_by_filename(result)
                    else:
                        annotation_dict = result
            elif self.annotations_type == "coco":
                annotation_dict, _ = load_coco_from_file(annotations_file)
            elif self.annotations_type == "mot":
                mot_kwargs = {}
                if "image_width" in self.additional_args:
                    mot_kwargs["image_width"] = self.additional_args["image_width"]
                if "image_height" in self.additional_args:
                    mot_kwargs["image_height"] = self.additional_args["image_height"]
                if "video_name" in self.additional_args:
                    mot_kwargs["video_file"] = self.additional_args["video_name"]
                if annotations_file.is_dir():
                    # Detect whether this is an fs layout (videos/ + labels/) or a single MOT dir
                    video_dir_name = self.additional_args.get("video_dir_name", "videos")
                    label_dir_name = self.additional_args.get("label_dir_name", "labels")
                    if (annotations_file / label_dir_name).is_dir():
                        mot_results = load_mot_from_fs(
                            annotations_file,
                            image_width=mot_kwargs.get("image_width"),
                            image_height=mot_kwargs.get("image_height"),
                            video_dir_name=video_dir_name,
                            label_dir_name=label_dir_name,
                        )
                        annotation_dict = self._key_mot_fs_annotations_by_filename(mot_results)
                    else:
                        video_anns, _ = load_mot_from_dir(annotations_file, **mot_kwargs)
                        annotation_dict = self._key_video_annotations_by_filename(video_anns)
                elif annotations_file.suffix == ".zip":
                    video_anns, _ = load_mot_from_zip(annotations_file, **mot_kwargs)
                    annotation_dict = self._key_video_annotations_by_filename(video_anns)
                else:
                    video_anns, _ = load_mot_from_dir(annotations_file, **mot_kwargs)
                    annotation_dict = self._key_video_annotations_by_filename(video_anns)
            elif self.annotations_type == "cvat_video":
                cvat_kwargs = {}
                if "image_width" in self.additional_args:
                    cvat_kwargs["image_width"] = self.additional_args["image_width"]
                if "image_height" in self.additional_args:
                    cvat_kwargs["image_height"] = self.additional_args["image_height"]
                if annotations_file.is_dir():
                    raw = load_cvat_from_fs(annotations_file, **cvat_kwargs)
                    annotation_dict = self._key_cvat_fs_annotations_by_filename(raw)
                elif annotations_file.suffix == ".zip":
                    result = load_cvat_from_zip(annotations_file, **cvat_kwargs)
                    if self._determine_cvat_annotation(result) == "video":
                        annotation_dict = self._key_video_annotations_by_filename(result)
                    else:
                        annotation_dict = result
                else:
                    result = load_cvat_from_xml_file(annotations_file, **cvat_kwargs)
                    if self._determine_cvat_annotation(result) == "video":
                        annotation_dict = self._key_video_annotations_by_filename(result)
                    else:
                        annotation_dict = result
            else:
                raise ValueError(f"Unsupported annotation type: {self.annotations_type}")

            return annotation_dict

    @staticmethod
    def _determine_cvat_annotation(result: CVATAnnotations) -> Literal["video", "image"]:
        """Determine whether a CVAT loader result contains video or image annotations."""
        if isinstance(result, IRVideoSequence):
            return "video"
        return "image"

    def _key_video_annotations_by_filename(
        self,
        video_data: CVATAnnotations,
    ) -> Dict[str, Sequence[IRTaskAnnotation]]:
        """Flatten video annotations into a single entry keyed by the source video path."""
        video_name = self.additional_args.get("video_name")
        if isinstance(video_data, IRVideoSequence):
            sequence_name = self._resolve_video_annotation_key(video_data.filename, fallback=video_name)
            return {sequence_name: video_data.to_annotations()}

        if video_name is None:
            video_name = self._first_video_annotation_filename(video_data.values())
        if video_name is None:
            video_name = self.annotations_file.stem

        all_anns: List[IRTaskAnnotation] = []
        for frame_anns in video_data.values():
            all_anns.extend(frame_anns)
        return {video_name: all_anns}

    def _key_cvat_fs_annotations_by_filename(
        self, fs_annotations: Mapping[str, CVATAnnotations]
    ) -> Dict[str, Sequence[IRTaskAnnotation]]:
        flattened: Dict[str, List[IRTaskAnnotation]] = {}
        for rel_path, result in fs_annotations.items():
            if isinstance(result, IRVideoSequence):
                video_key = self._resolve_video_annotation_key(result.filename, fallback=str(rel_path))
                flattened.setdefault(video_key, [])
                flattened[video_key].extend(result.to_annotations())
            elif isinstance(result, dict):  # CVATImageAnnotations: Dict[str, Sequence[IRImageAnnotationBase]]
                for filename, anns in result.items():
                    flattened.setdefault(filename, [])
                    flattened[filename].extend(anns)
        return flattened

    def _key_mot_fs_annotations_by_filename(
        self,
        fs_annotations: Mapping[Path, Tuple[IRVideoSequence, MOTContext]],
    ) -> Dict[str, Sequence[IRTaskAnnotation]]:
        flattened: Dict[str, List[IRTaskAnnotation]] = {}
        for rel_path, (sequence, _) in fs_annotations.items():
            rel_path_str = self._stringify_video_path(rel_path)
            sequence_name = self.annotations_file.stem if rel_path_str in (None, "", ".") else rel_path_str
            sequence_name = self._resolve_video_annotation_key(sequence.filename, fallback=sequence_name)
            flattened.setdefault(sequence_name, [])
            flattened[sequence_name].extend(sequence.to_annotations())
        return flattened

    @staticmethod
    def _stringify_video_path(path: Optional[Union[str, Path, PurePath]]) -> Optional[str]:
        if path is None:
            return None
        if isinstance(path, (Path, PurePath)):
            return path.as_posix()
        return str(path).replace("\\", "/")

    def _resolve_video_annotation_key(
        self,
        filename: Optional[Union[str, Path, PurePath]],
        fallback: Optional[str] = None,
    ) -> str:
        resolved = self._stringify_video_path(filename)
        if resolved not in (None, "", "."):
            return resolved

        resolved_fallback = self._stringify_video_path(fallback)
        if resolved_fallback not in (None, "", "."):
            return resolved_fallback
        return self.annotations_file.stem

    @classmethod
    def _first_video_annotation_filename(
        cls,
        frame_groups: Iterable[Sequence[IRAnnotationBase]],
    ) -> Optional[str]:
        for frame_anns in frame_groups:
            for ann in frame_anns:
                ann_filename = cls._stringify_video_path(ann.filename)
                if ann_filename not in (None, "", "."):
                    return ann_filename
        return None

    def download_annotations(self, dest_dir: Path):
        log_message("Downloading annotations from repository")
        repoApi = self.ds.source.repoApi
        if self.annotations_type in ("cvat", "cvat_video"):
            # Download just the annotation file
            repoApi.download(self.annotations_file.as_posix(), dest_dir, keep_source_prefix=True)
        elif self.annotations_type == "yolo":
            # Download the dataset .yaml file and the images + annotations
            # Download the file
            repoApi.download(self.annotations_file.as_posix(), dest_dir, keep_source_prefix=True)
            # Get the YOLO Context from the downloaded file
            meta_file = dest_dir / self.annotations_file
            context = YoloContext.from_yaml_file(meta_file, annotation_type=self.additional_args["yolo_type"])
            # Download the annotation data
            assert context.path is not None
            repoApi.download(self.annotations_file.parent / context.path, dest_dir, keep_source_prefix=True)
        elif self.annotations_type == "mot":
            repoApi.download(self.annotations_file.as_posix(), dest_dir, keep_source_prefix=True)
        elif self.annotations_type == "coco":
            # Download just the annotation file
            repoApi.download(self.annotations_file.as_posix(), dest_dir, keep_source_prefix=True)

    @staticmethod
    def determine_load_location(ds: "Datasource", annotations_path: Union[str, Path]) -> AnnotationLocation:
        # Local files take priority
        if Path(annotations_path).exists():
            return "disk"

        # Try to find it in the repo otherwise
        try:
            files = ds.source.repoApi.list_path(Path(annotations_path).as_posix())
            if len(files) > 0:
                return "repo"
        except PathNotFoundError:
            pass

        # TODO: handle repo bucket too

        raise AnnotationsNotFoundError(annotations_path)

    def remap_annotations(
        self,
        annotations: Mapping[str, Sequence[IRTaskAnnotation]],
        remap_func: Optional[Callable[[str], Optional[str]]] = None,
    ) -> Mapping[str, Sequence[IRTaskAnnotation]]:
        """
        Remaps the filenames in the annotations to the datasource's data points.

        Args:
            annotations: Annotations to remap
            remap_func: Function that maps from an annotation path to a datapoint path. \
                If None, we try to guess it by getting a datapoint and remapping that path
        """
        if not annotations:
            return {}

        if remap_func is None:
            first_ann = list(annotations.keys())[0]
            first_ann_filename = Path(first_ann).name
            queried = self.ds["path"].endswith(first_ann_filename).select("size").all()
            dp_paths = [dp.path for dp in queried]
            remap_func = self.guess_annotation_filename_remapping(first_ann, dp_paths)

        remapped = {}

        for filename, anns in annotations.items():
            new_filename = remap_func(filename)
            if new_filename is None:
                log_message(
                    f'Skipping annotation with filename "{filename}" because it could not be mapped to a datapoint'
                )
                continue
            for ann in anns:
                if isinstance(ann, IRVideoAnnotationTrack):
                    for track_ann in ann.annotations:
                        track_ann.filename = new_filename
                    continue

                if ann.filename is not None:
                    ann.filename = remap_func(ann.filename)
                else:
                    if not self.is_video_format:
                        raise ValueError(f"Non-video annotation has no filename: {ann}")
                    ann.filename = new_filename
            remapped[new_filename] = anns

        return remapped

    @staticmethod
    def guess_annotation_filename_remapping(
        annotation_path: str, datapoint_paths: List[str]
    ) -> Callable[[str], Optional[str]]:
        """
        Guesses the remapping function from the annotations to the data points.

        Args:
            annotation_path: path of an existing annotations
            datapoint_paths: paths of the data points in the datasource that end with the filename of this annotation
        """

        if len(datapoint_paths) == 0:
            raise ValueError(f"No datapoints found that match the annotation path {annotation_path}")

        dp_path = datapoint_paths[0]

        if len(datapoint_paths) > 1:
            # TODO: Maybe prompt user to choose a fitting datapoint (ordered by similarity)
            dp_path = AnnotationImporter.get_best_fit_datapoint_path(annotation_path, datapoint_paths)
            log_message(f'Multiple datapoints found for annotation path "{annotation_path}". Using "{dp_path}"')

        return AnnotationImporter.generate_path_map_func(annotation_path, dp_path)

    @staticmethod
    def generate_path_map_func(ann_path: str, dp_path: str) -> Callable[[str], Optional[str]]:
        # Using os-dependent path for ann_path because we're getting it from the importer,
        # which will return os-dependent paths
        ann_path_obj = PurePath(ann_path)
        dp_path_posix = PurePosixPath(dp_path)

        matcher = SequenceMatcher(
            None,
            ann_path_obj.parts,
            dp_path_posix.parts,
        )
        diff = matcher.get_matching_blocks()

        # Make sure that both sequences have the same end, get the common part.
        # Then the rest is going to be the prefix that is either added or subtracted.

        # We need there to be only one match that is at the very end, otherwise we throw an error
        if len(diff) != 2:
            raise CannotRemapPathError(ann_path, dp_path)

        match = diff[0]
        # Make sure that the match goes until the end
        if match.a + match.size != len(ann_path_obj.parts) or match.b + match.size != len(dp_path_posix.parts):
            raise CannotRemapPathError(ann_path, dp_path)
        # ONE of the paths need to go until the start
        if match.a != 0 and match.b != 0:
            raise CannotRemapPathError(ann_path, dp_path)

        # If the match is total, just return identity
        if match.a == 0 and match.b == 0:

            def identity_func(x: str) -> str:
                # Do a replace because we might be going from a windows path to a posix path
                return x.replace(ann_path, dp_path)

            return identity_func

        # The function that maps ends up being:
        # - Get the common part of the path
        # - Either remove the remainder, or add the prefix, depending on which is longer

        if match.b > match.a:
            # Add a prefix
            prefix = dp_path_posix.parts[match.a : match.b]

            def add_prefix(x: str) -> Optional[str]:
                return PurePath(*prefix, x).as_posix()

            return add_prefix

        else:
            # Remove the prefix
            def remove_prefix(x: str) -> Optional[str]:
                p = PurePath(x)
                if len(p.parts) <= match.a:
                    return None
                return PurePath(*p.parts[match.a :]).as_posix()

            return remove_prefix

    @staticmethod
    def get_best_fit_datapoint_path(ann_path: str, datapoint_paths: List[str]) -> str:
        """
        Get the datapoint path that is the closest to the annotation path.

        Args:
            ann_path: path of an annotation
            datapoint_paths: paths of the data points in the datasource that end with the filename of this annotation
        """
        best_match: Optional[str] = None
        best_match_length: Optional[int] = None

        for dp_path in datapoint_paths:
            ann_path_posix = PurePosixPath(ann_path)
            dp_path_posix = PurePosixPath(dp_path)

            matcher = SequenceMatcher(
                None,
                ann_path_posix.parts,
                dp_path_posix.parts,
            )
            diff = matcher.get_matching_blocks()

            if len(diff) != 2:  # Has multiple matches - bad
                continue
            match = diff[0]
            if match.a != 0 and match.b != 0:
                continue

            # Exact match - perfect!
            if match.a == 0 and match.b == 0:
                return dp_path

            if best_match_length is None or match.size > best_match_length:
                best_match = dp_path
                best_match_length = match.size
        if best_match is None:
            raise ValueError(f"No good match found for annotation path {ann_path} in the datasource.")
        return best_match

    def convert_to_ls_tasks(self, annotations: Mapping[str, Sequence[IRTaskAnnotation]]) -> Mapping[str, bytes]:
        """
        Converts the annotations to Label Studio tasks.
        """
        if self.is_video_format:
            return self._convert_to_ls_video_tasks(annotations)
        current_user_id = UserAPI.get_current_user(self.ds.source.repoApi.host).user_id
        tasks = {}
        for filename, anns in annotations.items():
            t = LabelStudioTask(user_id=current_user_id)
            t.data["image"] = self.ds.source.raw_path(filename)
            t.add_ir_annotations(anns)
            tasks[filename] = t.model_dump_json().encode("utf-8")
        return tasks

    def _convert_to_ls_video_tasks(
        self, annotations: Mapping[str, Sequence[IRTaskAnnotation]]
    ) -> Mapping[str, bytes]:
        """
        Converts video annotations to Label Studio video tasks.
        """
        tasks = {}
        for filename, anns in annotations.items():
            sequence = self._build_video_sequence(anns, filename)
            if sequence is None:
                continue
            video_path = self.ds.source.raw_path(filename)
            ls_task = video_ir_to_ls_video_task(sequence, video_path=video_path)
            if ls_task is not None:
                tasks[filename] = ls_task.model_dump_json().encode("utf-8")
        return tasks

    @staticmethod
    def _build_video_sequence(
        annotations: Sequence[IRTaskAnnotation],
        filename: str,
    ) -> Optional[IRVideoSequence]:
        tracks = [ann for ann in annotations if isinstance(ann, IRVideoAnnotationTrack)]
        frame_annotations = [ann for ann in annotations if isinstance(ann, IRVideoBBoxFrameAnnotation)]
        if frame_annotations:
            tracks.extend(build_video_sequence_from_annotations(frame_annotations).tracks)
        if not tracks:
            return None

        sequence = IRVideoSequence.from_annotations(tracks=tracks, filename=filename)
        sequence.resolved_video_width()
        sequence.resolved_video_height()
        sequence.resolved_sequence_length()
        return sequence
