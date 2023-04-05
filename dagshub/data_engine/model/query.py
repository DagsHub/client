import logging
from typing import Any, Dict, TYPE_CHECKING

from dagshub.data_engine import DEFAULT_NAMESPACE
if TYPE_CHECKING:
    from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)

class Query:
    def __init__(self, dataset: "Dataset"):
        self.dataset = dataset

    def compose(self, other_query: "Query") -> "Query":
        return Query()

    @staticmethod
    def from_dict(ds: "Dataset", query_dict: Dict[str, Any]):
        return Query(ds)
