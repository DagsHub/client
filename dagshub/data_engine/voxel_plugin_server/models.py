from typing import Optional, TYPE_CHECKING, Any, List

from dataclasses import dataclass

from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.model.query import QueryFilterTree

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


@dataclass
class VoxelFilterState:
    _CLS: str
    exclude: bool
    isMatching: bool
    range: Optional[List[Any]]
    values: Optional[List[Any]]
    filter_field: Optional[str]

    def to_datasource_query(self) -> QueryFilterTree:
        # TODO: handle exclude and isMatching
        if self.range is not None:
            # range: field >= min AND field <= max
            resQuery = QueryFilterTree()
            if self.range[0] is not None:
                q1 = QueryFilterTree(self.filter_field)
                q1.compose("ge", self.range[0])
                resQuery.compose("and", q1)
            if self.range[1] is not None:
                q2 = QueryFilterTree(self.filter_field)
                q2.compose("le", self.range[1])
                resQuery.compose("and", q2)
            return resQuery

        if self.values is not None:
            #
            res_q = QueryFilterTree()
            for val in self.values:
                q = QueryFilterTree(self.filter_field)
                q.compose("eq", val)
                res_q.compose("or", q)
            return res_q

        raise NotImplementedError
