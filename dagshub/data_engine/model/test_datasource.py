import pandas as pd
import pytest

from dagshub.data_engine.model.datasource import DataSource, DataPointMetadataUpdateEntry


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

    actual = DataSource._df_to_metadata(metadata_df)
    expected = [
        DataPointMetadataUpdateEntry("test1", "key1", "1", "INTEGER"),
        DataPointMetadataUpdateEntry("test1", "key2", "4.0", "FLOAT"),
        DataPointMetadataUpdateEntry("test1", "key3", "7", "STRING"),
        DataPointMetadataUpdateEntry("test2", "key1", "2", "INTEGER"),
        DataPointMetadataUpdateEntry("test2", "key2", "5.0", "FLOAT"),
        DataPointMetadataUpdateEntry("test2", "key3", "8", "STRING"),
        DataPointMetadataUpdateEntry("test3", "key1", "3", "INTEGER"),
        DataPointMetadataUpdateEntry("test3", "key2", "6.0", "FLOAT"),
        DataPointMetadataUpdateEntry("test3", "key3", "9", "STRING"),
    ]
    assert expected == actual


@pytest.mark.parametrize("column", ["key3", 3])
def test_column_arg(metadata_df, column):
    actual = DataSource._df_to_metadata(metadata_df, column)
    expected = [
        DataPointMetadataUpdateEntry("7", "file", "test1", "STRING"),
        DataPointMetadataUpdateEntry("7", "key1", "1", "INTEGER"),
        DataPointMetadataUpdateEntry("7", "key2", "4.0", "FLOAT"),
        DataPointMetadataUpdateEntry("8", "file", "test2", "STRING"),
        DataPointMetadataUpdateEntry("8", "key1", "2", "INTEGER"),
        DataPointMetadataUpdateEntry("8", "key2", "5.0", "FLOAT"),
        DataPointMetadataUpdateEntry("9", "file", "test3", "STRING"),
        DataPointMetadataUpdateEntry("9", "key1", "3", "INTEGER"),
        DataPointMetadataUpdateEntry("9", "key2", "6.0", "FLOAT"),
    ]
    assert expected == actual


def test_fails_with_nonstring_path(metadata_df):
    with pytest.raises(Exception):
        DataSource._df_to_metadata(metadata_df, "key2")


def test_fails_out_of_bounds(metadata_df):
    with pytest.raises(Exception):
        DataSource._df_to_metadata(metadata_df, 10)


def test_fails_nonexistent_field(metadata_df):
    with pytest.raises(Exception):
        DataSource._df_to_metadata(metadata_df, "dgsdfgsdg")
