import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from dagshub.data_engine.model.datasource import Datasource, _reject_brotli_parquet


def _write_parquet(path, compression):
    table = pa.table({"path": ["a.txt"], "value": [1]})
    pq.write_table(table, path, compression=compression)


def test_reject_brotli_parquet(tmp_path):
    path = tmp_path / "meta.parquet"
    _write_parquet(path, "brotli")

    with pytest.raises(ValueError, match="Brotli"):
        _reject_brotli_parquet(str(path))


def test_snappy_parquet_is_allowed(tmp_path):
    path = tmp_path / "meta.parquet"
    _write_parquet(path, "snappy")

    _reject_brotli_parquet(str(path))
    frame = Datasource._convert_file_to_df(str(path))

    assert frame["path"].tolist() == ["a.txt"]
