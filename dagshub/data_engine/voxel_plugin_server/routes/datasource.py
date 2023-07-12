import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

logger = logging.getLogger(__name__)


async def get_fields(request: Request):
    plugin_state = get_plugin_state(request)
    ds = plugin_state.datasource
    return JSONResponse([a.to_json() for a in ds.source.metadata_fields])


async def update_metadata(request: Request):
    plugin_state = get_plugin_state(request)
    ds = plugin_state.datasource
    res = await request.json()
    return JSONResponse(res)
