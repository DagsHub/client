import pytest

from dagshub.data_engine.client.models import MetadataFieldSchema, MetadataFieldType
from dagshub.data_engine.model import datasources
from dagshub.data_engine.model.datasource import Datasource


@pytest.fixture
def ds():
    ds_state = datasources.DatasourceState(name="test-dataset", repo="kirill/repo")
    ds_state.metadata_fields = [
        MetadataFieldSchema("col1", MetadataFieldType.STRING, False),
        MetadataFieldSchema("col_int", MetadataFieldType.INTEGER, False),
    ]
    ds_state.path = "repo://kirill/repo/data/"
    yield Datasource(ds_state)
