class WrongOrderError(Exception):
    def __init__(self, other_type: type):
        super().__init__()
        self.other_type = other_type

    def __str__(self):
        return (
            f"Can't have a dataset to the right of {self.other_type}.\r\n"
            f"Make sure to use parentheses to chain logical and/or operators.\r\n"
            f"Example: `ds[(ds['col1'] > 1) & (ds['col2'] < 3)])`"
        )


class DatasetFieldComparisonError(Exception):
    def __str__(self):
        return (
            "Can't compare two fields in a dataset between each other.\r\n"
            "Querying only supports comparisons with primitives (int/str/float)"
        )


class WrongOperatorError(Exception):
    pass


class FieldNotFoundError(Exception):
    def __init__(self, field: str):
        super().__init__()
        self.field = field

    def __str__(self):
        return f"Field {self.field} does not exist on this datasource"


class DataEngineGqlError(Exception):
    def __init__(self, original_exception, support_id):
        super().__init__()
        self.original_exception = original_exception
        self.support_id = support_id

    def __str__(self):
        return (
            f"Original exception: {self.original_exception.__class__.__name__} - {self.original_exception} \n"
            f"Support Id: {self.support_id}"
        )


class DatasourceAlreadyExistsError(Exception):
    def __init__(self, datasource):
        super().__init__()
        self.datasource = datasource

    def __str__(self):
        return f"Datasource with name {self.datasource.name} already exists in repository {self.datasource.repo}"


class DatasourceNotFoundError(Exception):
    def __init__(self, datasource):
        super().__init__()
        self.datasource = datasource

    def __str__(self):
        return (
            f"Datasource with name {self.datasource.name} or id {self.datasource.id} not found "
            f"in repository {self.datasource.repo}"
        )


class DatasetNotFoundError(Exception):
    def __init__(self, repo, id, name):
        super().__init__()
        self.repo = repo
        self.id = id
        self.name = name

    def __str__(self):
        return f"Dataset with name {self.name} or id {self.id} not found " f"in repository {self.repo}"


class LSInitializingError(Exception):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Label Studio on DagsHub is starting up! Please try again in a couple of seconds"
