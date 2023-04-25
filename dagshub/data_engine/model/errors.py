class WrongOrderError(Exception):
    def __init__(self, other_type: type):
        super().__init__()
        self.other_type = other_type

    def __str__(self):
        return f"Can't have a dataset to the right of {self.other_type}.\r\n" \
               f"Make sure to use parentheses to chain logical and/or.\r\n" \
               f"Example: `ds[(ds['col1'] > 1) & (ds['col2'] < 3)])`"


class DatasetFieldComparisonError(Exception):
    def __str__(self):
        return f"Can't compare two fields in a dataset between each other.\r\n" \
               f"Querying only supports comparisons with primitives (int/str/float)"


class WrongOperatorError(Exception):
    pass
