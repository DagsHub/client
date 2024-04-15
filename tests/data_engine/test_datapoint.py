from dagshub.data_engine.client.models import DatasourceType


def test_getitem_metadata(some_datapoint):
    for key in some_datapoint.metadata:
        assert some_datapoint[key] == some_datapoint.metadata[key]


def test_download_url_encoding(some_datapoint):
    some_datapoint.path = "aaa # bbb/file.txt"
    some_datapoint.datasource.source.source_type = DatasourceType.REPOSITORY
    download_url = some_datapoint.download_url
    assert "#" not in download_url
    assert download_url.endswith("aaa%20%23%20bbb/file.txt")
