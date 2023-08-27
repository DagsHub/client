import enum


class ReservedTags(enum.Enum):
    ANNOTATION = "annotation"


class DagshubDataType:
    def __init__(self, value):
        self.tags = []
        self.value = value

    def as_annotation(self):
        self.tags.append(ReservedTags.ANNOTATION.value)
        return self

    def is_annotation(self):
        return ReservedTags.ANNOTATION in self.tags

    def tag(self, tag):
        if tag not in ReservedTags._value2member_map_:
            self.tags.append(tag)
            return self
        raise ValueError("This tag is reserved, choose a different tag name")

class Int(DagshubDataType):
    pass


class String(DagshubDataType):
    pass


class Blob(DagshubDataType):
    pass


class Float(DagshubDataType):
    pass


class Bool(DagshubDataType):
    pass
