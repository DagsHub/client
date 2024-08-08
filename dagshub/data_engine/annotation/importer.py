from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Literal, Optional, Union, Sequence, Mapping, Callable, List

from dagshub_annotation_converter.converters.cvat import load_cvat_from_zip
from dagshub_annotation_converter.converters.yolo import load_yolo_from_fs
from dagshub_annotation_converter.formats.label_studio.task import LabelStudioTask
from dagshub_annotation_converter.formats.yolo import YoloContext
from dagshub_annotation_converter.ir.image.annotations.base import IRAnnotationBase

from dagshub.common.api import UserAPI
from dagshub.common.api.repo import PathNotFoundError
from dagshub.common.helpers import log_message

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

AnnotationType = Literal["yolo", "cvat"]
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

    def import_annotations(self) -> Mapping[str, Sequence[IRAnnotationBase]]:
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
            annotation_dict: Mapping[str, Sequence[IRAnnotationBase]]
            if self.annotations_type == "yolo":
                annotation_dict, _ = load_yolo_from_fs(
                    annotation_type=self.additional_args["yolo_type"], meta_file=annotations_file
                )
            elif self.annotations_type == "cvat":
                annotation_dict = load_cvat_from_zip(annotations_file)

            return annotation_dict

    def download_annotations(self, dest_dir: Path):
        log_message("Downloading annotations from repository")
        repoApi = self.ds.source.repoApi
        if self.annotations_type == "cvat":
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
        annotations: Mapping[str, Sequence[IRAnnotationBase]],
        remap_func: Optional[Callable[[str], Optional[str]]] = None,
    ) -> Mapping[str, Sequence[IRAnnotationBase]]:
        """
        Remaps the filenames in the annotations to the datasource's data points.

        Args:
            annotations: Annotations to remap
            remap_func: Function that maps from an annotation path to a datapoint path. \
                If None, we try to guess it by getting a datapoint and remapping that path
        """
        if remap_func is None:
            first_ann = list(annotations.keys())[0]
            first_ann_filename = PurePosixPath(first_ann).name
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
                assert ann.filename is not None
                ann.filename = remap_func(ann.filename)
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
        ann_path_posix = PurePosixPath(ann_path)
        dp_path_posix = PurePosixPath(dp_path)

        matcher = SequenceMatcher(
            None,
            ann_path_posix.parts,
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
        if match.a + match.size != len(ann_path_posix.parts) or match.b + match.size != len(dp_path_posix.parts):
            raise CannotRemapPathError(ann_path, dp_path)
        # ONE of the paths need to go until the start
        if match.a != 0 and match.b != 0:
            raise CannotRemapPathError(ann_path, dp_path)

        # If the match is total, just return identity
        if match.a == 0 and match.b == 0:

            def identity_func(x: str) -> str:
                return x.replace(ann_path, dp_path)

            return identity_func

        # The function that maps ends up being:
        # - Get the common part of the path
        # - Either remove the remainder, or add the prefix, depending on which is longer

        if match.b > match.a:
            # Add a prefix
            prefix = dp_path_posix.parts[match.a : match.b]

            def add_prefix(x: str) -> Optional[str]:
                return PurePosixPath(*prefix, x).as_posix()

            return add_prefix

        else:
            # Remove the prefix
            def remove_prefix(x: str) -> Optional[str]:
                p = PurePosixPath(x)
                if len(p.parts) <= match.a:
                    return None
                return PurePosixPath(*p.parts[match.a :]).as_posix()

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

    def convert_to_ls_tasks(self, annotations: Mapping[str, Sequence[IRAnnotationBase]]) -> Mapping[str, bytes]:
        """
        Converts the annotations to Label Studio tasks.
        """
        current_user_id = UserAPI.get_current_user(self.ds.source.repoApi.host).user_id
        tasks = {}
        for filename, anns in annotations.items():
            t = LabelStudioTask(user_id=current_user_id)
            t.data["image"] = self.ds.source.raw_path(filename)
            t.add_ir_annotations(anns)
            tasks[filename] = t.model_dump_json().encode("utf-8")
        return tasks
