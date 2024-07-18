import dataclasses
import logging
from typing import TYPE_CHECKING, Type, Union, Set, Optional, Literal

from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.dtypes import DagshubDataType, MetadataFieldType, ReservedTags, ThumbnailType
from dagshub.data_engine.model.schema_util import metadataTypeLookup

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource

logger = logging.getLogger(__name__)


class MetadataFieldBuilder:
    """
    Builder class for changing properties of a metadata field in a datasource.
    It is also possible to create a new empty field with predefined schema with this builder.
    All functions return back the builder object to facilitate a builder pattern, for example::

        builder.set_type(bytes).set_annotation().apply()
    """

    def __init__(self, datasource: "Datasource", field_name: str):
        self.datasource = datasource

        self._field_name = field_name

        preexisting_schema = next(filter(lambda f: f.name == field_name, datasource.fields), None)

        # Make a copy of the dataclass, so we don't change the base schema
        if preexisting_schema is not None:
            preexisting_schema = dataclasses.replace(preexisting_schema)
            if preexisting_schema.tags is not None:
                preexisting_schema.tags = preexisting_schema.tags.copy()

        self._schema = preexisting_schema
        self.already_exists = self._schema is not None

    @property
    def schema(self) -> MetadataFieldSchema:
        if self._schema is None:
            raise RuntimeError(
                f"Field {self._field_name} is a new field. "
                "Make sure to set_type() the field before setting any other properties"
            )
        return self._schema

    def set_type(self, t: Union[Type, DagshubDataType]) -> "MetadataFieldBuilder":
        """
        Set the type of the field.
        The type can be either a Python primitive supported by the Data Engine
        (``str``, ``bool``, ``int``, ``float``, ``bytes``)
        or it can be a :class:`~dagshub.data_engine.dtypes.DagshubDataType` inheritor.
        The DataType inheritors can define additional tags on top of just the basic backing type
        """
        backing_type = self._get_backing_type(t)

        if self._schema is None:
            self._schema = MetadataFieldSchema(
                name=self._field_name, valueType=backing_type, multiple=False, tags=set()
            )
            if issubclass(t, DagshubDataType) and t.custom_tags is not None:
                self._schema.tags = t.custom_tags.copy()
        else:
            if backing_type != self._schema.valueType:
                raise ValueError(
                    "Can't change a type of an already existing field "
                    f"(changing from {self._schema.valueType.value} to {backing_type.value})"
                )
            if issubclass(t, DagshubDataType) and t.custom_tags is not None:
                self._add_tags(t.custom_tags)

        return self

    def set_annotation(self, is_annotation: bool = True) -> "MetadataFieldBuilder":
        """
        Mark or unmark the field as annotation field
        """
        self._set_or_unset(ReservedTags.ANNOTATION.value, is_annotation)
        return self

    def set_thumbnail(
        self,
        thumbnail_type: Optional[Literal["video", "audio", "image", "pdf", "text"]] = None,
        is_thumbnail: bool = True,
    ) -> "MetadataFieldBuilder":
        """
        Mark or unmark the field as thumbnail field, with the specified thumbnail type
        """

        # Remove thumbnail tag
        if not is_thumbnail:
            self._set_or_unset_thumbnails(ReservedTags.THUMBNAIL_VIZ.value, is_thumbnail)
            return self

        # Set thumbnail tag
        if thumbnail_type is None:
            raise ValueError("Thumbnail type must be specified")

        valid_types = ", ".join([t.value for t in ThumbnailType])
        try:
            thumbnail_type = ThumbnailType(thumbnail_type)
        except ValueError:
            raise ValueError(f"'{thumbnail_type}' is not a valid thumbnail type. Valid types are: {valid_types}")

        tag: ReservedTags

        if thumbnail_type == ThumbnailType.VIDEO:
            tag = ReservedTags.VIDEO
        elif thumbnail_type == ThumbnailType.AUDIO:
            tag = ReservedTags.AUDIO
        elif thumbnail_type == ThumbnailType.IMAGE:
            tag = ReservedTags.IMAGE
        elif thumbnail_type == ThumbnailType.PDF:
            tag = ReservedTags.PDF
        elif thumbnail_type == ThumbnailType.TEXT:
            tag = ReservedTags.TEXT
        else:
            raise ValueError(f"'{thumbnail_type}' is not a valid thumbnail type. Valid types are: {valid_types}")

        self._set_or_unset_thumbnails(tag, is_thumbnail)
        return self

    def _set_or_unset_thumbnails(self, type_tag, is_thumbnail):
        # Remove previous thumbnail type tags
        if self.schema.tags is not None:
            thumbnail_type_tags = {
                ReservedTags.VIDEO.value,
                ReservedTags.AUDIO.value,
                ReservedTags.IMAGE.value,
                ReservedTags.PDF.value,
                ReservedTags.TEXT.value,
            }

            for tag in thumbnail_type_tags:
                if tag in self.schema.tags:
                    self._remove_tag(tag)

        if is_thumbnail:
            self._add_tags({type_tag.value, ReservedTags.THUMBNAIL_VIZ.value})
        else:
            self._remove_tags(ReservedTags.THUMBNAIL_VIZ.value)

    def _set_or_unset(self, tag, is_set):
        if is_set:
            self._add_tags({tag})
        else:
            self._remove_tag(tag)

    def _add_tags(self, tags: Set[str]):
        if self.schema.tags is None:
            self.schema.tags = set()
        for t in tags:
            self.schema.tags.add(t)

    def _remove_tag(self, tag: str):
        if self.schema.tags is None:
            return
        try:
            self.schema.tags.remove(tag)
        except ValueError:
            logger.warning(f"Tag {tag} doesn't exist on the field, nothing to delete")

    def _remove_tags(self, *tags: str):
        if self.schema.tags is None:
            return
        for t in tags:
            self._remove_tag(t)

    @staticmethod
    def _get_backing_type(t: Union[Type, DagshubDataType]) -> MetadataFieldType:
        if issubclass(t, DagshubDataType):
            return t.backing_field_type

        if type(t) is type:
            if t not in metadataTypeLookup.keys():
                raise ValueError(f"Primitive type {type(t)} is not supported")
            return metadataTypeLookup[t]

        raise ValueError(f"{t} of type ({type(t)}) is not a valid primitive type or DagshubDataType")

    def apply(self):
        """
        Apply the outgoing changes to this metadata field.

        If you need to apply changes to multiple fields at once, use
        :func:`Datasource.apply_field_changes <dagshub.data_engine.model.datasource.Datasource.apply_field_changes>`
        instead.
        """
        self.datasource.apply_field_changes([self])
