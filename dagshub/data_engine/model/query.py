import datetime
import enum
import logging
from typing import Optional, Union, Dict

import pytz
from treelib import Tree, Node

from dagshub.data_engine.model.errors import WrongOperatorError
from dagshub.data_engine.model.schema_util import metadataTypeLookup, metadataTypeLookupReverse
from dagshub.data_engine.dtypes import MetadataFieldType

logger = logging.getLogger(__name__)


def bytes_deserializer(val: str) -> bytes:
    if val.startswith('b"') or val.startswith("b'"):
        return val[2:-1].encode()
    # Fallback - encode whatever we got from the server
    return val.encode()


_metadataTypeCustomConverters = {
    bool: lambda x: x.lower() == "true",
    bytes: bytes_deserializer,
    datetime.datetime: lambda x: datetime.datetime.fromtimestamp(int(x) / 1000).astimezone(pytz.utc),
}


class FieldFilterOperand(enum.Enum):
    EQUAL = "EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL_THAN = "GREATER_EQUAL_THAN"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL_THAN = "LESS_EQUAL_THAN"
    CONTAINS = "CONTAINS"
    IS_NULL = "IS_NULL"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    DATE_TIME_FILTER = "DATE_TIME_FILTER"


class FieldFilterDateTimeFilter(enum.Enum):
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    TIMEOFDAY = "TIMEOFDAY"


dt_range_ops = [
    FieldFilterDateTimeFilter.YEAR,
    FieldFilterDateTimeFilter.MONTH,
    FieldFilterDateTimeFilter.DAY,
    FieldFilterDateTimeFilter.TIMEOFDAY,
]


fieldFilterOperandMap = {
    "eq": FieldFilterOperand.EQUAL,
    "gt": FieldFilterOperand.GREATER_THAN,
    "ge": FieldFilterOperand.GREATER_EQUAL_THAN,
    "lt": FieldFilterOperand.LESS_THAN,
    "le": FieldFilterOperand.LESS_EQUAL_THAN,
    "contains": FieldFilterOperand.CONTAINS,
    "isnull": FieldFilterOperand.IS_NULL,
    "startswith": FieldFilterOperand.STARTS_WITH,
    "endswith": FieldFilterOperand.ENDS_WITH,
    "date_time_filter": FieldFilterOperand.DATE_TIME_FILTER,
}

fieldFilterDateTimeFilterMap = {
    "year": FieldFilterDateTimeFilter.YEAR,
    "month": FieldFilterDateTimeFilter.MONTH,
    "day": FieldFilterDateTimeFilter.DAY,
    "timeofday": FieldFilterDateTimeFilter.TIMEOFDAY,
}
fieldFilterOperandMapReverseMap: Dict[str, str] = {}

for k, v in fieldFilterOperandMap.items():
    fieldFilterOperandMapReverseMap[v.value] = k

for k, v in fieldFilterDateTimeFilterMap.items():
    fieldFilterOperandMapReverseMap[v.value] = k

UNFILLED_NODE_TAG = "undefined"


class QueryFilterTree:
    def __init__(
        self,
        column_or_query: Optional[Union[str, "QueryFilterTree"]] = None,
        field_as_of: Optional[int] = None,
    ):
        self._operand_tree: Tree = Tree()

        if type(column_or_query) is str:
            # If it's ds["column"] then the root node is just the column name, will be filled later
            data: Dict[str, Union[str, int]] = {"field": column_or_query}
            if field_as_of is not None:
                data["as_of"] = int(field_as_of)
            self._operand_tree.create_node(UNFILLED_NODE_TAG, data=data)
        elif column_or_query is not None:
            self._operand_tree.create_node(column_or_query)

    def __repr__(self):
        if self.is_empty:
            return "Query: empty"
        return f"Query: {self.tree_to_dict()}"

    @property
    def column_filter(self) -> Optional[str]:
        filter_node = self._column_filter_node
        if filter_node is None:
            return None
        return filter_node.data["field"]

    def compose(self, op: str, other: Optional[Union[str, int, float, "QueryFilterTree", datetime.datetime]]):
        """
        Compose the current query with another query or a value using the specified operator.

        Args:
            op (str): The operator to use for composing the query.
            other (Optional[Union[str, int, float, "QueryFilterTree", datetime.datetime]]):
                The query or value to compose with.

        Raises:
            RuntimeError: If the operation is not supported or if there is a mismatch in usage.

        Notes:
            - If the current query contains only a column filter,
                it will be composed into a tree with the specified operator and value.
            - If the operation is 'isnull', it can only be applied to a column filter;
                otherwise, a RuntimeError is raised.
            - If the operation is 'not', a 'not' node is added to the query tree.
            - If either query is empty, the composition is adjusted accordingly.

        Example:
            ```
            ds['col1'] > 5
            ds['col2'].is_null()
            ```
            The above queries can be composed as:
            ```
            (ds['col1'] > 5) & (ds['col2'].is_null())
            ```
        """
        if self._column_filter_node is not None:
            # If there was an unfilled query node with a column - put the operand in that node
            node = self._column_filter_node
            node.tag = op
            node.data.update({"value": other})
        elif op == "isnull":
            # Can only do isnull on the column filter, if we got here, there's something wrong
            raise RuntimeError("is_null operation can only be done on a column (e.g. ds['col1'].is_null())")
        elif op == "not":
            new_tree = Tree()
            not_node = new_tree.create_node("not")
            new_tree.paste(not_node.identifier, self._operand_tree)
            self._operand_tree = new_tree
        else:
            # The other side is an actual query with its own tree - make a subtree
            if type(other) is not QueryFilterTree:
                raise RuntimeError(f"Expected other argument to be a dataset, got {type(other)} instead")
            if op not in ["and", "or"]:
                raise RuntimeError(
                    f"Cannot use operator '{op}' to chain two queries together.\r\n"
                    f"Queries:\r\n"
                    f"\t{self}\r\n"
                    f"\t{other}\r\n"
                )
            # Don't compose with an empty query, carry the other instead
            if self.is_empty:
                self._operand_tree = other._operand_tree
                return
            elif other.is_empty and other._column_filter_node is None:
                return
            composite_tree = Tree()
            root_node = composite_tree.create_node(op)
            composite_tree.paste(root_node.identifier, self._operand_tree)
            composite_tree.paste(root_node.identifier, other._operand_tree)
            self._operand_tree = composite_tree

    @property
    def _column_filter_node(self) -> Node:
        return next(self._operand_tree.filter_nodes(lambda n: n.tag == UNFILLED_NODE_TAG), None)

    @property
    def _operand_root(self) -> Node:
        return self._operand_tree[self._operand_tree.root]

    def serialize(self) -> Optional[Dict]:
        if self.is_empty:
            return None
        return self._serialize_node(self._operand_root, self._operand_tree)

    @staticmethod
    def _serialize_node(node: Node, tree: Tree) -> Dict:
        operand = node.tag
        if operand in ["and", "or"]:
            # recursively serialize children subqueries
            return {operand: [QueryFilterTree._serialize_node(child, tree) for child in tree.children(node.identifier)]}
        if operand == "not":
            assert len(tree.children(node.identifier)) == 1
            child = tree.children(node.identifier)[0]
            serialized = QueryFilterTree._serialize_node(child, tree)
            serialized["not"] = True
            return serialized
        else:
            # op can be a simple comparator, or a type of timeFilter
            query_op = fieldFilterOperandMap.get(operand) or fieldFilterDateTimeFilterMap.get(operand)
            if query_op is None:
                raise WrongOperatorError(f"Operator {operand} is not supported")
            key = node.data["field"]
            value = node.data["value"]
            as_of = node.data.get("as_of")

            value_type = metadataTypeLookup[type(value)].value if type(value) in metadataTypeLookup else None

            # if one of basic value types:
            if value_type:
                if type(value) is bytes:
                    # TODO: this will need to probably be changed when we allow actual binary field comparisons
                    value = value.decode("utf-8")
                else:
                    if isinstance(value, datetime.datetime):
                        value = int(value.timestamp() * 1000)
                    else:
                        value = str(value)

            if value_type is None and query_op not in dt_range_ops:
                raise RuntimeError(
                    f"Value type {value_type} is not supported for querying.\r\n"
                    f"Supported types: {list(metadataTypeLookup.keys())}"
                )
            res = {
                "filter": {
                    "key": key,
                    "value": str(value),
                    "valueType": value_type,
                    "comparator": query_op.value,
                }
            }

            if as_of:
                res["filter"]["asOf"] = as_of

            if query_op in dt_range_ops:
                # value is the actual node value in timeofday ("HH:mm-HH:mm"),
                # else, we use valueRange, so unset value
                res["filter"]["value"] = value if query_op is FieldFilterDateTimeFilter.TIMEOFDAY else 0
                # value type from client perspective is string or list,
                # but we need to tell backend to get datetime from db
                res["filter"]["valueType"] = MetadataFieldType.DATETIME.value
                # we use valueRange unless the node op is timeofday,
                # else, we use value, so unset valueRange
                res["filter"]["valueRange"] = 0 if query_op is FieldFilterDateTimeFilter.TIMEOFDAY else value
                # timeFilter replaces comparator
                res["filter"]["timeFilter"] = query_op.value
                # comparator indicates that timeFilter replaces comparator
                res["filter"]["comparator"] = FieldFilterOperand.DATE_TIME_FILTER.value

            return res

    @staticmethod
    def deserialize(serialized_query: Dict) -> "QueryFilterTree":
        q = QueryFilterTree()
        op_tree = Tree()
        QueryFilterTree._deserialize_node(serialized_query, op_tree)
        q._operand_tree = op_tree
        return q

    @staticmethod
    def _deserialize_node(node_dict: Dict, tree: Tree, parent_node=None) -> None:
        keys = list(node_dict.keys())
        if len(keys) == 0:
            return

        is_negative = node_dict.get("not", False)
        if is_negative:
            # If operation is negative - prepend a "not" node to the node we'll be adding
            neg_node = Node(tag="not")
            tree.add_node(neg_node, parent_node)
            parent_node = neg_node

        op_type = keys[0]
        val = node_dict[op_type]
        # Types: and, or, filter
        if op_type == "filter":
            comparator = fieldFilterOperandMapReverseMap[val["comparator"]]
            key = val["key"]
            if comparator.upper() == FieldFilterOperand.DATE_TIME_FILTER.value:
                # if comparator indicates that timeFilter replaced comparator,
                # we need to rebuild node carefully

                # value type must ignore actual value and be later set to MetadataFieldType.DATETIME
                value_type = None

                if val["timeFilter"] == FieldFilterDateTimeFilter.TIMEOFDAY.value:
                    value = val["value"]
                else:
                    value = val["valueRange"]

                # timeFilter replaced comparator in query, so now the reverse action
                comparator = val["timeFilter"].lower()
            else:
                value_type = metadataTypeLookupReverse[val["valueType"]]
                converter = _metadataTypeCustomConverters.get(value_type, lambda x: value_type(x))
                value = converter(val["value"])
            as_of = val.get("asOf")
            node = Node(tag=comparator, data={"field": key, "value": value, "as_of": as_of})
            tree.add_node(node, parent_node)
        elif op_type in ("and", "or"):
            main_node = Node(tag=op_type)
            tree.add_node(main_node, parent_node)
            for nested_node in val:
                QueryFilterTree._deserialize_node(nested_node, tree, main_node)
        else:
            raise RuntimeError(f"Unknown serialized query dict: {node_dict}")

    def tree_to_dict(self):
        return self._operand_tree.to_dict(with_data=True)

    def __deepcopy__(self, memodict={}):
        q = QueryFilterTree()
        q._operand_tree = Tree(tree=self._operand_tree, deep=True)
        return q

    @property
    def is_empty(self):
        return self._operand_tree.root is None or self._column_filter_node is not None
