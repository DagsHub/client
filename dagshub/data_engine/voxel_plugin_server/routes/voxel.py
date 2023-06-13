import logging
from typing import Dict, TYPE_CHECKING, List

import dacite
from starlette.requests import Request
from starlette.responses import JSONResponse

from dagshub.data_engine.model.query import DatasourceQuery
from dagshub.data_engine.voxel_plugin_server.models import VoxelFilterState
from dagshub.data_engine.voxel_plugin_server.utils import get_plugin_state

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource
    import fiftyone as fo

logger = logging.getLogger(__name__)


async def save_dataset(request: Request):
    plugin_state = get_plugin_state(request)
    filters = await get_voxel_filters(request)
    ds_with_filters = apply_filters_to_datasource(plugin_state.datasource, filters)
    print(f"Filters: {filters}")
    print(f"New filter: {ds_with_filters.get_query().serialize_graphql()}")
    return JSONResponse(f"Got {len(filters)} filters")


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


_generated_fields = ["dagshub_download_url"]


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
                min_val, max_val = dataset.bounds(col)
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
    voxel_query = DatasourceQuery()
    for f in filters:
        filter_query = f.to_datasource_query()
        voxel_query.compose("and", filter_query)
    return ds.add_query_op("and", voxel_query)
