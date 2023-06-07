import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING

from packaging import version

from dagshub.common.util import lazy_load

if TYPE_CHECKING:
    import fiftyone.core.media as fom
    import fiftyone.utils.annotations as foua
    import fiftyone.core.labels as fol
    import label_studio_sdk as ls
    import fiftyone.utils.labelstudio as foul
else:
    foua = lazy_load("fiftyone.utils.annotations", "fiftyone")
    foul = lazy_load("fiftyone.utils.labelstudio", "fiftyone")
    fom = lazy_load("fiftyone.core.media", "fiftyone")
    fol = lazy_load("fiftyone.core.labels", "fiftyone")
    ls = lazy_load("label_studio_sdk", "label-studio-sdk")

logger = logging.getLogger(__name__)


class DagsHubLabelStudioBackendConfig(foua.AnnotationBackendConfig):
    def __init__(
        self,
        name,
        label_schema,
        media_field="filepath",
        url=None,
        api_key=None,
        project_name=None,
        **kwargs,
    ):
        super().__init__(name, label_schema, media_field=media_field, **kwargs)

        self.url = url
        self.project_name = project_name

        self._api_key = api_key

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value

    def load_credentials(self, url=None, api_key=None):
        self._load_parameters(url=url, api_key=api_key)


class DagsHubLabelStudioBackend(foua.AnnotationBackend):
    """
    Class for interacting with the Label Studio annotation backend.
    Huge shoutout to Rustem Galiullin for writing the initial implementation of LS Backend for Voxel
    """

    @property
    def supported_media_types(self):
        return [fom.IMAGE]

    @property
    def supported_label_types(self):
        return [
            "classification",
            "detection",
            "detections",
            "instance",
            "instances",
            "polyline",
            "polylines",
            "polygon",
            "polygons",
            "keypoint",
            "keypoints",
            "segmentation",
            "scalar",
        ]

    @property
    def supported_scalar_types(self):
        return []

    @property
    def supported_attr_types(self):
        return []

    @property
    def supports_keyframes(self):
        return False

    @property
    def supports_video_sample_fields(self):
        return False

    @property
    def requires_label_schema(self):
        return True

    def _connect_to_api(self):
        return DagsHubLabelStudioAnnotationAPI(
            url=self.config.url, api_key=self.config.api_key
        )

    def upload_annotations(self, samples, anno_key, launch_editor=False):
        api = self.connect_to_api()

        logger.info("Uploading media to Label Studio...")
        results = api.upload_samples(samples, anno_key, self)
        logger.info("Upload complete")

        if launch_editor:
            results.launch_editor()

        return results

    def download_annotations(self, results):
        api = self.connect_to_api()

        logger.info("Downloading labels from Label Studio...")
        annotations = api.download_annotations(results)
        logger.info("Download complete")

        return annotations


class DagsHubLabelStudioAnnotationAPI(foua.AnnotationAPI):
    """A class to upload tasks and predictions to and fetch annotations from
    Label Studio.

    On initialization, the class will check if the server is reachable.
    """

    def __init__(self, url, api_key):
        self.url = url
        self._api_key = api_key
        self.backend = "dagshub-labelstudio"
        self._min_server_version = "1.4.0"

        self._setup()

    def _setup(self):
        if self._api_key is None:
            self._api_key = self._prompt_api_key(self.backend)

        self._client = ls.Client(self.url, self._api_key)
        self._client.check_connection()
        self._verify_server_version()

    def _verify_server_version(self):
        server_version = self._client.make_request(
            "GET", "/api/version"
        ).json()["release"]
        if not version.parse(server_version) >= version.parse(
            self._min_server_version
        ):
            raise ValueError(
                "Current Label Studio integration is only compatible with "
                "version>=%s" % self._min_server_version
            )

    def _init_project(self, config, samples):
        """Creates a new project on Label Studio.

        If project_name is not set in the configs, it will be generated.
        If project_name exists on the server, a timestamp will be added
        to the project name.

        Args:
            config: a :class:`LabelStudioBackendConfig`
            samples: a :class:`fiftyone.core.collections.SampleCollection`

        Returns:
            a ``label_studio_sdk.Project``
        """
        project_name = deepcopy(config.project_name)
        label_schema = deepcopy(config.label_schema)

        if project_name is None:
            _dataset_name = samples._root_dataset.name.replace(" ", "_")
            project_name = "FiftyOne_%s" % _dataset_name

        # if project name take, add timestamp
        projects = self._client.list_projects()
        for one in projects:
            if one.params["title"] == project_name:
                time_str = str(int(datetime.timestamp(datetime.now())))
                project_name += "_%s" % time_str
                break

        # generate label config
        assert len(label_schema) == 1
        _, label_info = label_schema.popitem()
        label_config = foul.generate_labeling_config(
            media=samples.media_type,
            label_type=label_info["type"],
            labels=label_info["classes"],
        )

        project = self._client.start_project(
            title=project_name, label_config=label_config
        )
        return project

    def _prepare_tasks(self, samples, label_schema, media_field):
        """Prepares Label Studio tasks for the given data."""
        samples.compute_metadata()

        ids, mime_types, filepaths = samples.values(
            ["id", "metadata.mime_type", media_field]
        )

        tasks = [
            {
                "source_id": _id,
                "media_type": "image",
                "mime_type": _mime_type,
                "image": _filepath,
            }
            for _id, _mime_type, _filepath in zip(ids, mime_types, filepaths)
        ]

        predictions, id_map = {}, {}
        for label_field, label_info in label_schema.items():
            if label_info["existing_field"]:
                predictions[label_field] = {
                    smp.id: foul.export_label_to_label_studio(
                        smp[label_field],
                        full_result={
                            "from_name": "label",
                            "to_name": "image",
                            "original_width": smp.metadata["width"],
                            "original_height": smp.metadata["height"],
                            "image_rotation": getattr(smp, "rotation", 0),
                        },
                    )
                    for smp in samples.select_fields(label_field)
                }
                id_map[label_field] = {
                    smp.id: foul._get_label_ids(smp[label_field])
                    for smp in samples.select_fields(label_field)
                }

        return tasks, predictions, id_map

    def _upload_tasks(self, project, tasks, predictions=None):
        """Uploads files to Label Studio and registers them as tasks.

        Args:
            project: a ``label_studio_sdk.Project``
            tasks: a list of task dicts
            predictions (None): optional predictions to upload

        Returns:
            a dict mapping ``task_id`` to ``sample_id``
        """
        files = [
            (
                one["source_id"],
                (
                    one["source_id"],
                    open(one[one["media_type"]], "rb"),
                    one["mime_type"],
                ),
            )
            for one in tasks
        ]

        # upload files first and get their upload ids
        upload_resp = self._client.make_request(
            "POST",
            f"/api/projects/{project.id}/import",
            params={"commit_to_project": True},
            files=files,
        )

        # create tasks out of the uploaded files
        payload = json.dumps(
            {
                "file_upload_ids": upload_resp.json()["file_upload_ids"],
                "files_as_tasks_list": False,
            }
        )
        self._client.headers.update({"Content-Type": "application/json"})
        self._client.make_request(
            "POST", f"/api/projects/{project.id}/reimport", data=payload
        )

        # get uploaded task ids
        uploaded_ids = project.get_tasks(only_ids=True)[-len(files):]
        uploaded_tasks = {
            i: t["source_id"] for i, t in zip(uploaded_ids, tasks)
        }

        # upload predictions if given
        if predictions:
            source2task = {v: k for k, v in uploaded_tasks.items()}
            for _, label_predictions in predictions.items():
                ls_predictions = [
                    {
                        "task": source2task[smp_id],
                        "result": pred,
                    }
                    for smp_id, pred in label_predictions.items()
                ]
                project.create_predictions(ls_predictions)

        return uploaded_tasks

    @staticmethod
    def _get_matched_labeled_tasks(project, task_ids):
        matched_tasks = project.get_tasks(selected_ids=task_ids)

        def task_filter(x):
            return x["is_labeled"] or bool(x.get("predictions"))

        return list(filter(task_filter, matched_tasks))

    def _import_annotations(self, tasks, task_map, label_type):
        results = {}
        for t in tasks:
            # convert latest annotation results
            if t["is_labeled"]:
                annotations = t.get("annotations", [])
            else:
                annotations = t.get("predictions", [])

            latest_annotation = (
                annotations[-1]
                if len(annotations) == 0
                else sorted(annotations, key=lambda x: x["updated_at"])[-1]
            )
            if label_type == "keypoints":
                labels = foul.import_label_studio_annotation(
                    latest_annotation["result"]
                )
            else:
                labels = [
                    foul.import_label_studio_annotation(r)
                    for r in latest_annotation.get("result", [])
                ]

            # add to dict
            if labels:
                label_ids = (
                    {l.id: l for l in labels}
                    if not isinstance(labels[0], fol.Regression)
                    else labels[0]
                )
                sample_id = task_map[t["id"]]
                results[sample_id] = label_ids

        return results

    def _export_to_label_studio(self, labels, label_type):
        if foul._LABEL_TYPES[label_type]["multiple"] is None:
            return foul.export_label_to_label_studio(labels)

        return [foul.export_label_to_label_studio(l) for l in labels]

    def upload_samples(self, samples, anno_key, backend):
        """Uploads the given samples to Label Studio according to the given
        backend's annotation and server configuration.

        Args:
            samples: a :class:`fiftyone.core.collections.SampleCollection`
            anno_key: the annotation key
            backend: a :class:`LabelStudioBackend` to use to perform the upload

        Returns:
            a :class:`LabelStudioAnnotationResults`
        """
        config = backend.config

        project = self._init_project(config, samples)

        tasks, predictions, id_map = self._prepare_tasks(
            samples,
            config.label_schema,
            config.media_field,
        )
        uploaded_tasks = self._upload_tasks(project, tasks, predictions)

        # TODO: implement (:
        return None

        return LabelStudioAnnotationResults(
            samples,
            config,
            anno_key,
            id_map,
            project.id,
            uploaded_tasks,
            backend=backend,
        )

    def download_annotations(self, results):
        """Downloads the annotations from the Label Studio server for the given
        results instance and parses them into the appropriate FiftyOne types.

        Args:
            results: a :class:`LabelStudioAnnotationResults`

        Returns:
            the annotations dict
        """
        project = self._client.get_project(results.project_id)
        labeled_tasks = self._get_matched_labeled_tasks(
            project, list(results.uploaded_tasks.keys())
        )
        annotations = {}
        for label_field, label_info in results.config.label_schema.items():
            return_type = foua._RETURN_TYPES_MAP[label_info["type"]]
            labels = self._import_annotations(
                labeled_tasks, results.uploaded_tasks, return_type
            )
            annotations.update({label_field: {return_type: labels}})

        return annotations

    def upload_predictions(self, project, tasks, sample_labels, label_type):
        """Uploads the given predictions to an existing Label Studio project.

        Args:
            project: a ``label_studio_sdk.Project``
            tasks: a list of task dicts
            sample_labels: a list or list of lists of
                :class:`fiftyone.core.labels.Label` instances
            label_type: the label type string
        """
        for task, labels in zip(tasks, sample_labels):
            predictions = self._export_to_label_studio(labels, label_type)
            project.create_prediction(task, predictions)

    def delete_tasks(self, task_ids):
        """Deletes the given tasks from Label Studio.

        Args:
            task_ids: list of task ids
        """
        for t_id in task_ids:
            self._client.make_request(
                "DELETE",
                f"/api/tasks/{t_id}",
            )

    def delete_project(self, project_id):
        """Deletes the project from Label Studio.

        Args:
            project_id: project id
        """
        self._client.make_request(
            "DELETE",
            f"/api/projects/{project_id}",
        )
