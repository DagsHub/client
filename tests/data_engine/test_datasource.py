import pandas as pd
import pytest

from dagshub.data_engine.client.models import MetadataFieldType
from dagshub.data_engine.model.datasource import Datasource, DatapointMetadataUpdateEntry


@pytest.fixture
def metadata_df():
    data_dict = {
        "file": ["test1", "test2", "test3"],
        "key1": [1, 2, 3],
        "key2": [4.0, 5.0, 6.0],
        "key3": ["7", "8", "9"]
    }
    return pd.DataFrame.from_dict(data_dict)


def test_default_behavior(metadata_df):
    print(metadata_df.dtypes)

    actual = Datasource._df_to_metadata(metadata_df)
    expected = [
        DatapointMetadataUpdateEntry("test1", "key1", "1", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("test1", "key2", "4.0", MetadataFieldType.FLOAT),
        DatapointMetadataUpdateEntry("test1", "key3", "7", MetadataFieldType.STRING),
        DatapointMetadataUpdateEntry("test2", "key1", "2", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("test2", "key2", "5.0", MetadataFieldType.FLOAT),
        DatapointMetadataUpdateEntry("test2", "key3", "8", MetadataFieldType.STRING),
        DatapointMetadataUpdateEntry("test3", "key1", "3", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("test3", "key2", "6.0", MetadataFieldType.FLOAT),
        DatapointMetadataUpdateEntry("test3", "key3", "9", MetadataFieldType.STRING),
    ]
    assert expected == actual


@pytest.mark.parametrize("column", ["key3", 3])
def test_column_arg(metadata_df, column):
    actual = Datasource._df_to_metadata(metadata_df, column)
    expected = [
        DatapointMetadataUpdateEntry("7", "file", "test1", MetadataFieldType.STRING),
        DatapointMetadataUpdateEntry("7", "key1", "1", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("7", "key2", "4.0", MetadataFieldType.FLOAT),
        DatapointMetadataUpdateEntry("8", "file", "test2", MetadataFieldType.STRING),
        DatapointMetadataUpdateEntry("8", "key1", "2", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("8", "key2", "5.0", MetadataFieldType.FLOAT),
        DatapointMetadataUpdateEntry("9", "file", "test3", MetadataFieldType.STRING),
        DatapointMetadataUpdateEntry("9", "key1", "3", MetadataFieldType.INTEGER),
        DatapointMetadataUpdateEntry("9", "key2", "6.0", MetadataFieldType.FLOAT),
    ]
    assert expected == actual


def test_fails_with_nonstring_path(metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(metadata_df, "key2")


def test_fails_out_of_bounds(metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(metadata_df, 10)


def test_fails_nonexistent_field(metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(metadata_df, "dgsdfgsdg")
