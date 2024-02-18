import logging
from typing import TYPE_CHECKING, List

import dacite
from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.data_engine.model.query import QueryFilterTree
from dagshub.data_engine.voxel_plugin_server.models import VoxelFilterState
from dagshub.data_engine.voxel_plugin_server.routes.util import error_handler
from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource
    import fiftyone as fo

logger = logging.getLogger(__name__)


@error_handler
async def save_dataset(request: Request):
    plugin_state = get_plugin_state(request)
    data = await request.json()
    name = data["name"]
    if data["saveVoxelFilters"]:
        filters = await get_voxel_filters(request)
        ds_with_filters = apply_filters_to_datasource(plugin_state.datasource, filters)
    else:
        ds_with_filters = plugin_state.datasource

    try:
        ds_with_filters.save_dataset(name)
        return JSONResponse(f"Dataset {name} saved successfully")
    except Exception as e:
        return JSONResponse(f"Error while saving dataset: {e}", status_code=400)


async def get_voxel_filters(request: Request) -> List[VoxelFilterState]:
    plugin_state = get_plugin_state(request)
    filter_dict = (await request.json())["filters"]

    def transform(field, filter_dict):
        filter = dacite.from_dict(VoxelFilterState, filter_dict)
        filter.filter_field = field
        return filter

    filters = [transform(k, v) for k, v in filter_dict.items()]
    filters = sanitize_voxel_filter(plugin_state.voxel_session, filters)
    return filters


_generated_fields = ["dagshub_download_url", "filepath", "id", "datapoint_id", "datapoint_path"]


def sanitize_voxel_filter(sess: "fo.Session", filters: List[VoxelFilterState]):
    """
    This command sanitizes the voxel filter dictionary.
    Included sanitization:
        - Range queries: check for min/max value in the range and remove the bounds
            if e.g. the min value is the same as the dataset's min value
        - Removes reserved/generated fields (like dagshub_download_url)
    """
    dataset = sess.dataset
    res_filters = []
    for f in filters:
        if f.filter_field in _generated_fields:
            logger.warning(f"Not applying filter to field {f.filter_field} because it's a generated field")
        else:
            # TODO: maybe get the metadata from the datasource and only filter for existing fields
            # Remove bounds for range queries
            if f.range is not None:
                min_val, max_val = dataset.bounds(f.filter_field)
                if f.range[0] == min_val:
                    f.range[0] = None
                if f.range[1] == max_val:
                    f.range[1] = None
                if f.range == [None, None]:
                    # Do not add if there are no bounds
                    continue
            res_filters.append(f)
    return res_filters


def apply_filters_to_datasource(ds: "Datasource", filters: List[VoxelFilterState]) -> "Datasource":
    """
    Apply a list of voxel filters to a given datasource.

    Args:
        ds (Datasource): The datasource to which the filters should be applied.
        filters (List[VoxelFilterState]): A list of voxel filters to be applied.

    Returns:
        Datasource: The modified datasource with the applied filters.
    """
    voxel_query = QueryFilterTree()
    for f in filters:
        filter_query = f.to_datasource_query()
        voxel_query.compose("and", filter_query)
    return ds.add_query_op("and", voxel_query)
