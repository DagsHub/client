import logging
from typing import Any, Dict
from collections import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)


class DatapointCollection(abc.MutableSequence[str]):

    def __init__(self, dataset: "Dataset"):
        self.dataset = dataset
