import enum
import logging
from typing import TYPE_CHECKING, Optional, Union

from treelib import Tree, Node

from dagshub.data_engine.model.errors import WrongOperatorError

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

logger = logging.getLogger(__name__)

_metadataTypeLookup = {
    type(0): "INTEGER",
    type(True): "BOOLEAN",
    type(0.5): "FLOAT",
    type("aaa"): "STRING",
}


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
    # TODO: turn on when ready
    # "ne": FieldFilterOperand.NOT_EQUAL,
    "gt": FieldFilterOperand.GREATER_THAN,
    "ge": FieldFilterOperand.GREATER_EQUAL_THAN,
    "lt": FieldFilterOperand.LESS_THAN,
    "le": FieldFilterOperand.LESS_EQUAL_THAN,
    "contains": FieldFilterOperand.CONTAINS,
}


class DataSourceQuery:
    def __init__(self, datasource: "Datasource", column_or_query: Optional[Union[str, "DataSourceQuery"]] = None):
        self.datasource = datasource

        self._operand_tree: Optional[Tree] = Tree()
        self._column_filter: Optional[str] = None  # for storing filters when user does ds["column"]
        if type(column_or_query) is str:
            # If it's ds["column"] then the root node is just the column name
            self._column_filter = column_or_query
        elif column_or_query is not None:
            self._operand_tree.create_node(column_or_query)

    def __str__(self):
        return f"<Query: {self.to_dict()}>"

    def compose(self, op: str, other: Union[str, int, float, "DataSourceQuery"]):
        if self._column_filter is not None:
            # Just the column is in the query - compose into a tree
            self._operand_tree.create_node(op, data={"field": self._column_filter, "value": other})
            self._column_filter = None
        else:
            # The query is an actual query with a tree - make a subtree
            if type(other) is not DataSourceQuery:
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

    @staticmethod
    def _serialize_node(node: Node, tree: Tree) -> dict:
        operand = node.tag
        if operand in ["and", "or"]:
            # recursively serialize children subqueries
            return {operand: [DataSourceQuery._serialize_node(child, tree) for child in tree.children(node.identifier)]}
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
                "filter": {
                    "key": key,
                    "value": str(value),
                    "valueType": value_type,
                    "comparator": query_op.value,
                }
            }

    def to_dict(self):
        return self._operand_tree.to_dict(with_data=True)

    def __deepcopy__(self, memodict={}):
        q = DataSourceQuery(self.datasource, None)
        if self._column_filter is not None:
            q._column_filter = self._column_filter
        else:
            q._operand_tree = Tree(tree=self._operand_tree, deep=True)
        return q

    @property
    def is_empty(self):
        return self._column_filter is not None or self._operand_tree.root is None
