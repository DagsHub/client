import enum
import logging
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING, List, Optional, Union

from treelib import Tree, Node

from dagshub.data_engine import DEFAULT_NAMESPACE
from dagshub.data_engine.model.errors import WrongOperatorError

if TYPE_CHECKING:
    from dagshub.data_engine.model.dataset import Dataset

logger = logging.getLogger(__name__)

_metadataTypeLookup = {
    type(0): "INTEGER",
    type(True): "BOOLEAN",
    type(0.5): "FLOAT",
    type("aaa"): "STRING",
}


@dataclass
class FieldFilter:
    field: str
    op: "FieldFilterOperand"
    val: Union[int, float, bool, str]

    def serialize_graphql(self):
        return {
            "key": self.field,
            "value": self.val,
            "valueType": _metadataTypeLookup[type(self.val)],
            "comparator": self.op.value,
        }

    def __str__(self):
        return f"<{self.field} {self.op.value} {self.val}>"


class FieldFilterOperand(enum.Enum):
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL_THAN = "GREATER_EQUAL_THAN"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL_THAN = "LESS_EQUAL_THAN"
    CONTAINS = "CONTAINS"


fieldFilterOperandMap = {
    "eq": FieldFilterOperand.EQUAL,
    "ne": FieldFilterOperand.NOT_EQUAL,
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


#
# class DatasetQuery:
#     def __init__(self, dataset: "Dataset", arg: Any):
#         self.dataset = dataset
#         # TODO: change from Any to an actual object
#         self.arg = arg


class DatasetQuery:
    def __init__(self, dataset: "Dataset", column_or_query: Optional[Union[str, "DatasetQuery"]] = None):
        self.dataset = dataset
        self.filter: Optional[QueryFilter] = None

        self._operand_tree: Optional[Tree] = Tree()
        self._column_filter: Optional[str] = None  # for storing filters when user does ds["column"]
        if type(column_or_query) is str:
            # If it's ds["column"] then the root node is just the column name
            self._column_filter = column_or_query
        elif column_or_query is not None:
            self._operand_tree.create_node(column_or_query)

    def __str__(self):
        return f"<Query: {self.to_dict()}>"

    def compose(self, op: str, other: Union[str, int, float, "DatasetQuery"]):
        if self._column_filter is not None:
            # Just the column is in the query - compose into a tree
            self._operand_tree.create_node(op, data={"field": self._column_filter, "value": other})
            self._column_filter = None
        else:
            # The query is an actual query with a tree - make a subtree
            if type(other) is not DatasetQuery:
                raise RuntimeError(f"Expected other argument to be a dataset, got {type(other)} instead")
            if op not in ["and", "or"]:
                raise RuntimeError(f"Cannot use operator '{op}' to chain two queries together.\r\n"
                                   f"Queries:\r\n"
                                   f"\t{self}\r\n"
                                   f"\t{other}\r\n")
            composite_tree = Tree()
            root_node = composite_tree.create_node(op)
            composite_tree.paste(root_node.identifier, self._operand_tree)
            composite_tree.paste(root_node.identifier, other._operand_tree)
            self._operand_tree = composite_tree

    @property
    def _operand_root(self) -> Node:
        return self._operand_tree[self._operand_tree.root]

    def serialize_graphql(self):
        if self.is_empty:
            return None
        return self._serialize_node(self._operand_root, self._operand_tree)
        #
        # return self.filter.serialize_graphql()

    @staticmethod
    def _serialize_node(node: Node, tree: Tree) -> dict:
        operand = node.tag
        if operand in ["and", "or"]:
            # recursively serialize children subqueries
            return {operand: [DatasetQuery._serialize_node(child, tree) for child in tree.children(node.identifier)]}
        else:
            query_op = fieldFilterOperandMap.get(operand)
            if query_op is None:
                raise WrongOperatorError(f"Operator {operand} is not supported")
            key = node.data["field"]
            value = node.data["value"]
            value_type = _metadataTypeLookup.get(type(value))
            if value_type is None:
                raise RuntimeError(f"Value type {value_type} is not supported for querying.\r\n"
                                   f"Supported types: {list(_metadataTypeLookup.keys())}")
            return {
                "key": key,
                "value": str(value),
                "valueType": value_type,
                "comparator": query_op.value,
            }

    def to_dict(self):
        return self._operand_tree.to_dict(with_data=True)

    @staticmethod
    def from_query_params(dataset: "Dataset", operand="and", **query_params) -> "Query":
        """
        Example usecase:
        Query(ds, name_contains="Data", date_eq = "2022-01-01")
        """
        q = DatasetQuery(dataset)
        params = q.parse_query_params(**query_params)
        q.filter = QueryFilter(QueryFilterOperand.from_str(operand), params)
        return q

    def __deepcopy__(self, memodict={}):
        q = DatasetQuery(self.dataset, None)
        if self._column_filter is not None:
            q._column_filter = self._column_filter
        else:
            q._operand_tree = Tree(tree=self._operand_tree, deep=True)
        return q

    @property
    def is_empty(self):
        return self._column_filter is not None or self._operand_tree.root is None

    def __oldcompose(self, other_query: "Query", operand="and") -> "Query":
        operand = QueryFilterOperand.from_str(operand)

        # If the operand is equal to the operand of the left-side query, "fold" the right side into the left side
        # AND ((AND (a, b), c) = AND (a, b, c)
        # OR (OR(a, AND(b, c)), d) = OR (a, AND(b, c), d)
        if self.filter is not None and operand == self.filter.op:
            self.filter.queries += other_query.filter.queries
            return self

        # Otherwise compose into a new query
        res = DatasetQuery(self.dataset)
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
