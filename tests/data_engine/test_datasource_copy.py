from dagshub.data_engine.client.gql_mutations import GqlMutations
from dagshub.data_engine.client.data_client import DataClient
from dagshub.data_engine.client.models import PreprocessingStatus
from dagshub.data_engine.model.datasource import Datasource
from dagshub.data_engine.model.datasource_state import DatasourceState


def test_copy_datasource_mutation_and_params():
    query = GqlMutations.copy_datasource().generate()

    assert "mutation copyDatasource" in query
    assert "$source: ID!" in query
    assert "$query: QueryInput" in query
    assert "copyDatasource(source: $source, name: $name, query: $query)" in query
    query_input = {"select": [{"name": "score", "alias": "confidence"}], "limit": 20}
    assert GqlMutations.copy_datasource_params(12, "snapshot", query_input) == {
        "source": 12,
        "name": "snapshot",
        "query": query_input,
    }


def test_copy_datasource_params_accept_latest_state():
    assert GqlMutations.copy_datasource_params("12", "latest", None)["query"] is None


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
                "origin": {
                    "sourceDatasourceId": "12",
                    "sourceRepoId": "7",
                    "sourceName": "source",
                    "sourceRootUrl": "repo://owner/repo/main:data",
                    "sourceType": "REPOSITORY",
                    "sourceBackingType": "postgres",
                    "creatorId": "3",
                    "createdAt": 1_700_000_001,
                    "query": '{"asOf":1700000000,"limit":20}',
                },
            }
        }

    monkeypatch.setattr(client, "_exec", fake_exec)
    query_input = {"asOf": 1_700_000_000, "limit": 20}
    result = client.copy_datasource(12, "snapshot", query_input)

    assert captured == {"source": 12, "name": "snapshot", "query": query_input}
    assert result.id == "13"
    assert result.preprocessingStatus == PreprocessingStatus.IN_PROGRESS
    assert result.origin is not None
    assert result.origin.sourceName == "source"
    assert result.origin.sourceBackingType == "postgres"


def test_datasource_copy_materializes_current_query(monkeypatch):
    state = object.__new__(DatasourceState)
    state.repo = "owner/repo"
    state.id = 12
    queried = Datasource(state).select("score").limit(5)
    captured = {}

    def fake_copy(repo, source, name):
        captured.update(repo=repo, source=source, name=name, query=source.serialize_gql_query_input())
        return "copied"

    monkeypatch.setattr("dagshub.data_engine.datasources.copy_datasource", fake_copy)

    assert queried.copy("projection") == "copied"
    assert captured["repo"] == "owner/repo"
    assert captured["source"] is queried
    assert captured["name"] == "projection"
    assert captured["query"] == {"select": [{"name": "score"}], "query": None, "limit": 5}
