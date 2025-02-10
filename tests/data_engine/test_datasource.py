import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from dagshub.data_engine.annotation import MetadataAnnotations
from dagshub.data_engine.client.models import MetadataFieldSchema
from dagshub.data_engine.dtypes import MetadataFieldType, ReservedTags
from dagshub.data_engine.model.datapoint import Datapoint
from dagshub.data_engine.model.datasource import Datasource, DatapointMetadataUpdateEntry, MetadataContextManager
from dagshub.data_engine.model.metadata import wrap_bytes, MultipleDataTypesUploadedError, StringFieldValueTooLongError
from dagshub.data_engine.model.query_result import QueryResult
from tests.data_engine.util import add_string_fields, add_document_fields, add_annotation_fields


@pytest.fixture
def metadata_df():
    data_dict = {
        "file": ["test1", "test2", "test3"],
        "key1": [1, 2, 3],
        "key2": [4.0, 5.0, 6.0],
        "key3": ["7", "8", "9"],
    }
    return pd.DataFrame.from_dict(data_dict)


def test_default_behavior(ds, metadata_df):
    print(metadata_df.dtypes)

    actual = Datasource._df_to_metadata(ds, metadata_df)
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
def test_column_arg(ds, metadata_df, column):
    actual = Datasource._df_to_metadata(ds, metadata_df, column)
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


def test_fails_with_nonstring_path(ds, metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(ds, metadata_df, "key2")


def test_fails_out_of_bounds(ds, metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(ds, metadata_df, 10)


def test_fails_nonexistent_field(ds, metadata_df):
    with pytest.raises(Exception):
        Datasource._df_to_metadata(ds, metadata_df, "dgsdfgsdg")


def test_binary_metadata(ds):
    ctx = MetadataContextManager(ds)
    data = "aaa".encode()
    encoded_data = wrap_bytes(data)
    ctx.update_metadata("test.txt", {"binary_value": data})

    expected = DatapointMetadataUpdateEntry("test.txt", "binary_value", encoded_data, MetadataFieldType.BLOB)
    assert ctx.get_metadata_entries() == [expected]


def test_validation_cant_upload_multi_type(ds):
    with pytest.raises(MultipleDataTypesUploadedError):
        with ds.metadata_context() as ctx:
            ctx.update_metadata("a.txt", {"field": "value"})
            ctx.update_metadata("b.txt", {"field": 1})


def test_validation_upload_long_string(ds):
    add_string_fields(ds, "field")
    with pytest.raises(StringFieldValueTooLongError):
        with ds.metadata_context() as ctx:
            ctx.update_metadata("a.txt", {"field": "a" * 100_000})


def test_uploading_new_big_file_turns_it_to_document(ds):
    data = "a" * 100_000
    with ds.metadata_context() as ctx:
        ctx.update_metadata("a.txt", {"field": data})
    client_mock: MagicMock = ds.source.client

    expected_field_update = [
        MetadataFieldSchema(
            "field", valueType=MetadataFieldType.BLOB, multiple=False, tags={ReservedTags.DOCUMENT.value}
        )
    ]

    client_mock.update_metadata_fields.assert_called_with(ds, expected_field_update)

    expected_data_upload = [
        DatapointMetadataUpdateEntry(
            url="a.txt", key="field", value=wrap_bytes(data.encode("utf-8")), valueType=MetadataFieldType.BLOB
        )
    ]
    client_mock.update_metadata.assert_called_with(ds, expected_data_upload)


def test_uploading_to_document_turns_into_blob(ds):
    data = "aaa"
    field = "field"
    add_document_fields(ds, field)
    with ds.metadata_context() as ctx:
        ctx.update_metadata("a.txt", {field: data})

    client_mock: MagicMock = ds.source.client
    expected_data_upload = [
        DatapointMetadataUpdateEntry(
            url="a.txt", key=field, value=wrap_bytes(data.encode("utf-8")), valueType=MetadataFieldType.BLOB
        )
    ]
    client_mock.update_metadata.assert_called_with(ds, expected_data_upload)


def test_pandas_timestamp(ds):
    data_dict = {
        "file": ["test1", "test2"],
        "key1": [
            datetime.datetime(2020, 10, 10, 10, 10, 0),
            datetime.datetime(2030, 10, 10, 10, 20, 20),
        ],
    }
    df = pd.DataFrame.from_dict(data_dict)

    df["key1"] = pd.to_datetime(df["key1"])

    actual = ds._df_to_metadata(df)

    expected = [
        DatapointMetadataUpdateEntry(
            "test1", "key1", f"{int(data_dict['key1'][0].timestamp()) * 1000}", MetadataFieldType.DATETIME
        ),
        DatapointMetadataUpdateEntry(
            "test2", "key1", f"{int(data_dict['key1'][1].timestamp()) * 1000}", MetadataFieldType.DATETIME
        ),
    ]

    assert expected == actual


def _test_dataframe_annotation_addition(source_ds: Datasource, target_ds: Datasource):
    dp_path = "test1"
    annotation_field = "annotation"

    add_annotation_fields(source_ds, annotation_field)

    dp = Datapoint(datapoint_id=0, path=dp_path, metadata={"width": 100, "height": 100}, datasource=source_ds)

    ann = MetadataAnnotations(dp, annotation_field)
    ann.add_image_bbox("cat", 0.1, 0.1, 0.1, 0.1)
    dp.metadata[annotation_field] = ann

    qr = QueryResult([dp], datasource=source_ds, fields=[])
    df = qr.dataframe

    ls_task_bytes = ann.to_ls_task()
    assert ls_task_bytes is not None

    expected = [
        DatapointMetadataUpdateEntry(dp_path, annotation_field, wrap_bytes(ls_task_bytes), MetadataFieldType.BLOB)
    ]

    actual = target_ds._df_to_metadata(df)

    print(df)
    print(actual)

    assert expected == actual


# def test_annotation_in_dataframe(ds):
#     _test_dataframe_annotation_addition(ds, ds)
#
#
# def test_annotation_in_dataframe_to_new_datasource(ds, other_ds):
#     _test_dataframe_annotation_addition(ds, other_ds)
