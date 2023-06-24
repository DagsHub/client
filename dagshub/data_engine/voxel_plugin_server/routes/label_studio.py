import logging
from typing import Dict, Tuple, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.common.api.repo import RepoAPI
from dagshub.data_engine.voxel_plugin_server.label_studio_driver import LabelStudioDriver
from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

logger = logging.getLogger(__name__)

# Storage for label studio drivers
_ls_driver_store: Dict[Tuple[str, Optional[str]], LabelStudioDriver] = {}


async def to_labelstudio(request: Request):
    plugin_state = get_plugin_state(request)

    selected = plugin_state.voxel_session.selected_view
    print(selected)
    req_dicts = []
    if selected is None:
        return JSONResponse({"error": "Selection empty"}, status_code=400)
    for sample in selected:
        req_dicts.append({
            "id": sample["datapoint_id"],
            "downloadurl": sample["dagshub_download_url"],
        })
    print(f"Sending to annotation: {req_dicts}")
    # Don't open the project because we're going to open it from the Voxel's plugin code
    link = plugin_state.datasource.annotate_in_labelstudio(req_dicts, open_project=False)
    return JSONResponse({"link": link})


async def __to_labelstudio_old(request: Request):
    logger.info(await request.json())
    ls = get_or_create_ls_driver(request)
    return JSONResponse(await ls.annotate_selected())

    # repo_info = _api.get_repo_info()
    # return JSONResponse(repo_info.full_name)


def get_or_create_ls_driver(request: Request):
    _pluginState = get_plugin_state(request)
    _api: RepoAPI = _pluginState.datasource.source.repoApi
    _branch = _pluginState.branch
    key = (_api.repo_name, _branch)
    driver = _ls_driver_store.get(key, None)
    if driver is None:
        driver = LabelStudioDriver(_pluginState)
        _ls_driver_store[key] = driver
    return driver
