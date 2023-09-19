import logging
from typing import TYPE_CHECKING, Type, Union, List

from dagshub.data_engine.client.models import MetadataFieldSchema, ReservedTags
from dagshub.data_engine.dtypes import DagshubDataType, MetadataFieldType
from dagshub.data_engine.model.schema_util import metadataTypeLookup

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

logger = logging.getLogger(__name__)


class MetadataFieldBuilder:
    """
    Builder class for changing properties of a metadata field in a datasource.
    It is also possible to create a new empty field with predefined schema with this builder
    """

    def __init__(self, datasource: "Datasource", field_name: str):
        self.datasource = datasource

        self._field_name = field_name

        preexisting_schema = next(filter(lambda f: f.name == field_name, datasource.fields), None)

        self._schema = preexisting_schema
        self.already_exists = self._schema is not None

    @property
    def schema(self) -> MetadataFieldSchema:
        if self._schema is None:
            raise ValueError(f"Field {self._field_name} is a new field. "
                             f"Make sure to set_type() the field before setting any other properties")
        return self._schema

    def set_type(self, t: Union[Type, DagshubDataType]):
        backing_type = self._get_backing_type(t)

        if self._schema is None:
            self._schema = MetadataFieldSchema(
                name=self._field_name,
                valueType=backing_type,
                multiple=False,
                tags=None
            )
            if isinstance(t, DagshubDataType):
                self._schema.tags = t.custom_tags
        else:
            if backing_type != self._schema.valueType:
                raise ValueError("Can't change a type of an already existing field "
                                 f"(changing from {self._schema.valueType.value} to {backing_type.value})")
            if isinstance(t, DagshubDataType):
                self._add_tags(t.custom_tags)

    def set_annotation(self, is_annotation: bool = True):
        self._set_or_unset(ReservedTags.ANNOTATION.value, is_annotation)

    def _set_or_unset(self, tag, is_set):
        if is_set:
            self._add_tags([tag])
        else:
            self._remove_tag(tag)

    def _add_tags(self, tags: List[str]):
        if self._schema.tags is None:
            self._schema.tags = []
        self._schema.tags.extend(tags)

    def _remove_tag(self, tag: str):
        if self._schema.tags is None:
            return
        try:
            self._schema.tags.remove(tag)
        except ValueError:
            logger.warning(f"Tag {tag} doesn't exist on the field, nothing to delete")

    @staticmethod
    def _get_backing_type(t: Union[Type, DagshubDataType]) -> MetadataFieldType:
        if type(t) == type:
            if t not in metadataTypeLookup.keys():
                raise ValueError(f"Primitive type {type(t)} is not supported")
            return metadataTypeLookup[t]

        if isinstance(t, DagshubDataType):
            return t.backing_field_type

        raise ValueError(f"{t} of type ({type(t)}) is not a valid primitive type or DagshubDataType")

    def apply(self):
        self.datasource.apply_field_changes([self])
