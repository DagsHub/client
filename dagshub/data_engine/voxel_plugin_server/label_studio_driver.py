import asyncio
import logging

import fiftyone.core.labels

from dagshub.common.util import lazy_load
from dagshub.data_engine.voxel_plugin_server.dagshub_ls_backend import DagsHubLabelStudioBackendConfig
from dagshub.data_engine.voxel_plugin_server.models import PluginServerState, LabelStudioProject
from dagshub.data_engine.voxel_plugin_server.utils import set_voxel_envvars
from typing import Any, Dict, List, TYPE_CHECKING

import httpx

from dagshub.common.api.repo import RepoAPI

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import fiftyone as fo
    import fiftyone.utils.annotations as foua
    import fiftyone.utils.labelstudio as foul
else:
    fo = lazy_load("fiftyone")
    foua = lazy_load("fiftyone.utils.annotations", "fiftyone")
    foul = lazy_load("fiftyone.utils.labelstudio", "fiftyone")


class LabelStudioDriver:
    def __init__(self, plugin_state: PluginServerState):
        self.repo = plugin_state.repo

        self.branch = plugin_state.branch if plugin_state.branch is not None else self.repo.default_branch
        self.voxel_session = plugin_state.voxel_session

        # Spin up a new async client, so we can keep it async
        self.client = httpx.AsyncClient(base_url=self.repo.repo_url, timeout=1000.0, auth=self.repo.auth)

        self._ls_ready_task = None

        # self._annotation_backend = foul.LabelStudioBackend()
        # self._annotation_api = foul.LabelStudioAnnotationAPI(self.annotation_url, api_key=self.repo.auth.token)

    @property
    def is_workspace_ready(self):
        return self._ls_ready_task.done()

    @property
    def annotation_url(self):
        return self.repo.repo_url + "/annotations"

    async def ensure_workspace_running(self):
        # TODO: This actually doesn't track if the workspace got shut down
        # Launch the task
        if self._ls_ready_task is None:
            self._ls_ready_task = asyncio.create_task(self.start_workspace())
        # Wait for it to complete
        while not self.is_workspace_ready:
            await asyncio.sleep(0.3)

    async def run(self):
        await self.ensure_workspace_running()

        # await self.start_workspace()
        # print(await self.list_projects())
        # projects = await self.list_projects()
        # print(await self.list_storages(1))
        # await self.get_csrf()
        # await self.start_workspace()
        # await self.start_workspace()

    async def annotate_selected(self):
        self._patch_voxel_config()
        # self.voxel_session.selected
        # self.voxel_session.selected
        print(self.voxel_session.selected_view)
        # TODO debug stuff, cleanup
        anno_key = "some_test_labels"
        try:
            self.voxel_session.dataset.delete_annotation_run(anno_key)
        except:
            pass
        self.voxel_session.selected_view.annotate(
            anno_key=anno_key,
            backend="dagshub-labelstudio",
            label_field=self.get_label_field(),  # todo: need to figure out what to do here
            label_type="classification",
            classes=["field1", "field2"],
            api_key=self.repo.auth.token,
        )

        # foua.annotate(
        #     samples=self.voxel_session.selected,
        #     anno_key="some_test_labels"
        # )
        # return self.voxel_session.selected

    def _patch_voxel_config(self):
        fo.annotation_config.backends["dagshub-labelstudio"] = {
            "url": self.annotation_url,
            "config_cls": DagsHubLabelStudioBackendConfig.get_class_name()
        }

    def get_label_field(self):
        default_field = "dagshub_annotation"
        # TODO: logic to grab annotation field
        field = default_field
        active_dataset = self.voxel_session.dataset
        if active_dataset.has_field(field):
            # FIXME: remove the cleanup
            active_dataset.delete_sample_field(field)
        # if not active_dataset.has_field(field):
        #     active_dataset.add_sample_field(field_name=field, ftype=fiftyone.core.labels.Classification)
        return field

    async def get_all_projects(self) -> List[LabelStudioProject]:
        """
        NOTE: this is going to be slow on big projects because we need to do N queries for storages
        """
        projects = await self.list_projects()

        print(projects)

        async def generate_project_entry(list_proj_res: Dict[str, Any]) -> LabelStudioProject:
            id = list_proj_res["id"]
            storage_res = await self.list_storages(id)
            proj = LabelStudioProject(
                id=id,
                name=list_proj_res["title"],
                branch=storage_res[0]["revision"]
            )
            print(f"Project {id} storage: {storage_res}")
            return proj

        return await asyncio.gather(*(generate_project_entry(p) for p in projects))

    async def list_projects(self) -> Dict[str, Any]:
        resp = await self.client.get("/annotations/api/projects")
        return resp.json()["results"]

    async def list_storages(self, project_id: int) -> List[Dict[str, Any]]:
        resp = await self.client.get("/annotations/api/storages/", params={"project": project_id})
        return resp.json()

    async def start_workspace(self):
        await self.send_start_workspace()
        ready_url = "/annotations/ready"
        is_ready = False
        while not is_ready:
            print("Checking labelstudio workspace readiness...")
            resp = await self.send_request("get", ready_url)
            if resp.status_code == 404:
                # Likely label studio returned it (could be some permission error later)
                # Check that it's label studio actually, it will have "Label Studio" in title
                is_ready = b"Label Studio" in resp.content
                assert is_ready
                print("Got status code 404 from Label studio on ready check, workspace is ready")
            elif resp.status_code == 200:
                is_ready = "redirect" in resp.json()

            if not is_ready:
                print(f"Retrying in a bit")
                await asyncio.sleep(5.0)

    async def send_request(self, method, url, need_csrf=False, **kwargs):
        if need_csrf:
            if "data" not in kwargs:
                kwargs["data"] = {}
            kwargs["data"]["_csrf"] = await self.get_csrf()
        return await self.client.request(method, url, **kwargs)

    async def send_start_workspace(self):
        return await self.send_request("post", "annotations/start", need_csrf=True)

    async def get_csrf(self):
        if "_csrf" not in self.client.cookies:
            resp = await self.client.get("/")
            assert resp.status_code != 404
            self.client.cookies.update(resp.cookies)
        return self.client.cookies['_csrf']
