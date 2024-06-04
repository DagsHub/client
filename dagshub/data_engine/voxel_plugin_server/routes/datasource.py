import logging
from dataclasses import dataclass
from typing import Any

import dacite
from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.common.analytics import send_analytics_event
from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.model.schema_util import dacite_config
from dagshub.data_engine.voxel_plugin_server.routes.util import error_handler
from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

logger = logging.getLogger(__name__)


@error_handler
async def get_fields(request: Request):
    plugin_state = get_plugin_state(request)
    ds = plugin_state.datasource
    return JSONResponse([a.to_json() for a in ds.source.metadata_fields])


@dataclass
class UpdateMetadataRequestData:
    field: MetadataFieldSchema
    value: Any


@error_handler
async def update_metadata(request: Request):
    plugin_state = get_plugin_state(request)
    ds = plugin_state.datasource
    voxel_sess = plugin_state.voxel_session

    send_analytics_event("Client_DataEngine_addEnrichmentsWithVoxel", repo=ds.source.repoApi)

    req_data = dacite.from_dict(UpdateMetadataRequestData, await request.json(), config=dacite_config)
    datapoints = [sample["datapoint_path"] for sample in voxel_sess.selected_view]

    with ds.metadata_context() as ctx:
        ctx.update_metadata(datapoints, {req_data.field.name: req_data.value})

    return JSONResponse("OK")


@error_handler
async def refresh_dataset(request: Request):
    plugin_state = get_plugin_state(request)
    ds = plugin_state.datasource
    voxel_sess = plugin_state.voxel_session
    current_dataset = voxel_sess.dataset

    updated_dataset = ds.to_voxel51_dataset(name=current_dataset.name, force_download=True)
    updated_dataset.save()
    voxel_sess.refresh()

    return JSONResponse("OK")
