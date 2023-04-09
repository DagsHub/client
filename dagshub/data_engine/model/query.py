import enum
import logging
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING, List, Optional, Union

from dagshub.data_engine import DEFAULT_NAMESPACE

if TYPE_CHECKING:
    from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)


@dataclass
class FieldFilter:
    field: str
    op: "FieldFilterOperand"
    val: Union[int, float, bool, str]

    def serialize_graphql(self):
        return {
            "key": self.field,
            "value": self.val,
            "valueType": type(self.val).__name__,
            "comparator": self.op.value,
        }

    def __str__(self):
        return f"<{self.field} {self.op.value} {self.val}>"


class FieldFilterOperand(enum.Enum):
    EQUAL = "EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL_THAN = "GREATER_EQUAL_THAN"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL_THAN = "LESS_EQUAL_THAN"
    CONTAINS = "CONTAINS"


fieldFilterOperandMap = {
    "eq": FieldFilterOperand.EQUAL,
    "gt": FieldFilterOperand.GREATER_THAN,
    "ge": FieldFilterOperand.GREATER_EQUAL_THAN,
    "lt": FieldFilterOperand.LESS_THAN,
    "le": FieldFilterOperand.LESS_EQUAL_THAN,
    "contains": FieldFilterOperand.CONTAINS,
}


@dataclass
class QueryFilter:
    op: "QueryFilterOperand"
    queries: List[Union["Query", FieldFilter]]

    def serialize_graphql(self) -> dict:
        return {self.op.value.lower(): [
            q.serialize_graphql() for q in self.queries
        ]}

    def __str__(self):
        return f"<{self.op.value}: {[str(q) for q in self.queries]}>"


class QueryFilterOperand(enum.Enum):
    OR = "OR"
    AND = "AND"

    @staticmethod
    def from_str(operand: str) -> "QueryFilterOperand":
        operand = operand.lower()
        if operand == "and":
            return QueryFilterOperand.AND
        elif operand == "or":
            return QueryFilterOperand.OR
        else:
            raise RuntimeError(f"Unknown operand {operand}. Possible values: ['and', 'or']")


class Query:
    def __init__(self, dataset: "Dataset"):
        self.dataset = dataset
        self.filter: Optional[QueryFilter] = None

    def __str__(self):
        return f"<Query: Filter: {self.filter}>"

    def serialize_graphql(self):
        if self.filter is None:
            return None
        return self.filter.serialize_graphql()

    @staticmethod
    def from_query_params(dataset: "Dataset", operand="and", **query_params) -> "Query":
        """
        Example usecase:
        Query(ds, name_contains="Data", date_eq = "2022-01-01")
        """
        q = Query(dataset)
        params = q.parse_query_params(**query_params)
        q.filter = QueryFilter(QueryFilterOperand.from_str(operand), params)
        return q

    @property
    def is_empty(self):
        return self.filter is None or len(self.filter.queries) == 0

    def compose(self, other_query: "Query", operand="and") -> "Query":
        operand = QueryFilterOperand.from_str(operand)

        # If the operand is equal to the operand of the left-side query, "fold" the right side into the left side
        # AND ((AND (a, b), c) = AND (a, b, c)
        # OR (OR(a, AND(b, c)), d) = OR (a, AND(b, c), d)
        if self.filter is not None and operand == self.filter.op:
            self.filter.queries += other_query.filter.queries
            return self

        # Otherwise compose into a new query
        res = Query(self.dataset)
        queries = list(filter(lambda q: not q.is_empty, [self, other_query]))

        # If one of the queries is empty - ignore the composure and return the non-empty one
        if len(queries) == 1:
            return queries[0]

        op = QueryFilter(operand, queries)
        res.filter = op
        return res

    @staticmethod
    def parse_query_params(**params) -> List[FieldFilter]:
        separator = "_"
        res = []
        for filter_param, val in params.items():
            filter_separated = filter_param.split(separator)
            if len(filter_separated) < 2:
                raise RuntimeError(
                    f"Invalid query parameter: {filter_param}. Query params should have a format of '<field>_<operand>'")
            filter_field = filter_separated[:len(filter_separated) - 1]
            filter_operand = filter_separated[-1].lower()
            operand = fieldFilterOperandMap.get(filter_operand.lower())
            if operand is None:
                raise RuntimeError(
                    f"Invalid filter operand {filter_operand}.\nPossible values: {list(fieldFilterOperandMap.keys())}")
            res.append(FieldFilter(separator.join(filter_field), fieldFilterOperandMap[filter_operand], val))
        return res
