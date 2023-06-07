from typing import Optional, TYPE_CHECKING

from dagshub.common.api.repo import RepoAPI
from dataclasses import dataclass

if TYPE_CHECKING:
    import fiftyone as fo


@dataclass
class PluginServerState:
    voxel_session: "fo.Session"
    repo: RepoAPI
    branch: Optional[str] = None


@dataclass
class LabelStudioProject:
    id: int
    name: str
    branch: str
