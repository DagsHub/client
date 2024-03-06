from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.voxel_plugin_server.models import VoxelFilterState
from dagshub.data_engine.voxel_plugin_server.routes.voxel import apply_filters_to_datasource
from tests.data_engine.util import add_int_fields, add_string_fields


def test_range_filter(ds: Datasource):
    field_name = "field"
    add_int_fields(ds, field_name)
    filter = VoxelFilterState(
        _CLS="int", exclude=False, isMatching=True, range=[5, 10], values=None, filter_field=field_name
    )
    new_ds = apply_filters_to_datasource(ds, [filter])

    expected_ds = ds[(ds[field_name] >= 5) & (ds[field_name] <= 10)]
    assert new_ds.serialize_gql_query_input() == expected_ds.serialize_gql_query_input()


def test_lower_unbounded(ds: Datasource):
    field_name = "field"
    add_int_fields(ds, field_name)
    filter = VoxelFilterState(
        _CLS="int", exclude=False, isMatching=True, range=[None, 10], values=None, filter_field=field_name
    )
    new_ds = apply_filters_to_datasource(ds, [filter])

    expected_ds = ds[ds[field_name] <= 10]
    assert new_ds.serialize_gql_query_input() == expected_ds.serialize_gql_query_input()


def test_upper_unbounded(ds: Datasource):
    field_name = "field"
    add_int_fields(ds, field_name)
    filter = VoxelFilterState(
        _CLS="int", exclude=False, isMatching=True, range=[5, None], values=None, filter_field=field_name
    )
    new_ds = apply_filters_to_datasource(ds, [filter])

    expected_ds = ds[ds[field_name] >= 5]
    assert new_ds.serialize_gql_query_input() == expected_ds.serialize_gql_query_input()


def test_value_filter(ds: Datasource):
    field_name = "field"
    add_string_fields(ds, field_name)
    filter = VoxelFilterState(
        _CLS="str", exclude=False, isMatching=True, range=None, values=["a", "b", "c"], filter_field=field_name
    )

    new_ds = apply_filters_to_datasource(ds, [filter])

    expected_ds = ds[(ds[field_name] == "a") | (ds[field_name] == "b") | (ds[field_name] == "c")]
    assert new_ds.serialize_gql_query_input() == expected_ds.serialize_gql_query_input()


def test_composition(ds: Datasource):
    add_int_fields(ds, "field1", "field2")
    filter = VoxelFilterState(
        _CLS="int", exclude=False, isMatching=True, range=[5, None], values=None, filter_field="field1"
    )
    filter2 = VoxelFilterState(
        _CLS="int", exclude=False, isMatching=True, range=[None, 10], values=None, filter_field="field2"
    )
    new_ds = apply_filters_to_datasource(ds, [filter, filter2])

    expected_ds = ds[(ds["field1"] >= 5) & (ds["field2"] <= 10)]
    assert new_ds.serialize_gql_query_input() == expected_ds.serialize_gql_query_input()
