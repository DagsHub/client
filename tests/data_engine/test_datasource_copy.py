from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.models import PreprocessingStatus


def test_copy_datasource_mutation_and_params():
    query = GqlMutations.copy_datasource().generate()

    assert "mutation copyDatasource" in query
    assert "$source: ID!" in query
    assert "$asOf: DateTime" in query
    assert "copyDatasource(source: $source, name: $name, asOf: $asOf)" in query
    assert GqlMutations.copy_datasource_params(12, "snapshot", 1_700_000_000) == {
        "source": 12,
        "name": "snapshot",
        "asOf": 1_700_000_000,
    }


def test_copy_datasource_params_accept_latest_state():
    assert GqlMutations.copy_datasource_params("12", "latest", None)["asOf"] is None


def test_data_client_returns_copied_datasource(monkeypatch):
    client = object.__new__(DataClient)
    captured = {}

    def fake_exec(query, params):
        captured.update(params)
        return {
            "copyDatasource": {
                "id": "13",
                "name": "snapshot",
                "rootUrl": "repo://owner/repo/main:data",
                "integrationStatus": "VALID",
                "preprocessingStatus": "IN_PROGRESS",
                "type": "REPOSITORY",
            }
        }

    monkeypatch.setattr(client, "_exec", fake_exec)
    result = client.copy_datasource(12, "snapshot", 1_700_000_000)

    assert captured == {"source": 12, "name": "snapshot", "asOf": 1_700_000_000}
    assert result.id == "13"
    assert result.preprocessingStatus == PreprocessingStatus.IN_PROGRESS
