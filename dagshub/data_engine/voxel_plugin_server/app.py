import logging
from typing import Tuple, Dict, TYPE_CHECKING, Optional

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.common.api.repo import RepoAPI
from dagshub.data_engine.voxel_plugin_server.label_studio_driver import LabelStudioDriver
from dagshub.data_engine.voxel_plugin_server.models import PluginServerState
from dagshub.data_engine.voxel_plugin_server.utils import set_voxel_envvars

logger = logging.getLogger(__name__)

# Storage for label studio drivers
_ls_driver_store: Dict[Tuple[str, Optional[str]], LabelStudioDriver] = {}

app = Starlette(debug=True,
                middleware=[
                    Middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_methods=["*"],
                    ),
                ])


@app.route("/")
async def homepage(request):
    return JSONResponse({"Hello": "from the dagshub voxel dagshub server"})


def get_or_create_ls_driver(request: Request):
    _pluginState: PluginServerState = request.app.state.PLUGIN_STATE
    _api: RepoAPI = _pluginState.datasource.source.repoApi
    _branch = _pluginState.branch
    key = (_api.repo_name, _branch)
    driver = _ls_driver_store.get(key, None)
    if driver is None:
        driver = LabelStudioDriver(_pluginState)
        _ls_driver_store[key] = driver
    return driver


@app.route("/labelstudio/", methods=["POST"])
async def to_labelstudio(request: Request):
    logger.info(await request.json())
    ls = get_or_create_ls_driver(request)
    return JSONResponse(await ls.annotate_selected())

    # repo_info = _api.get_repo_info()
    # return JSONResponse(repo_info.full_name)


@app.route("/save_dataset", methods=["POST"])
async def save_dataset(request: Request):
    return JSONResponse({"Hello": "Saving query"})


async def spin_up_labelstudio(request: Request):
    ls = get_or_create_ls_driver(request)
