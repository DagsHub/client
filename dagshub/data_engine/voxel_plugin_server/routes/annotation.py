import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

logger = logging.getLogger(__name__)


async def to_annotate(request: Request):
    plugin_state = get_plugin_state(request)

    selected = plugin_state.voxel_session.selected_view
    print(selected)
    req_dicts = []
    if selected is None:
        return JSONResponse({"error": "Selection empty"}, status_code=400)
    for sample in selected:
        req_dicts.append({
            "id": sample["datapoint_id"],
            "download_url": sample["dagshub_download_url"],
        })
    print(f"Sending to annotation: {req_dicts}")
    # Don't open the project because we're going to open it from the Voxel's plugin code
    link = plugin_state.datasource.send_datapoints_to_annotation(req_dicts, open_project=False)
    return JSONResponse({"link": link})
