from typing import Optional, TYPE_CHECKING

from dataclasses import dataclass

from dagshub.data_engine.model.datasource import Datasource

if TYPE_CHECKING:
    import fiftyone as fo


@dataclass
class PluginServerState:
    voxel_session: "fo.Session"
    datasource: "Datasource"
    branch: Optional[str] = None


@dataclass
class LabelStudioProject:
    id: int
    name: str
    branch: str
