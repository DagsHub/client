import tempfile
from unittest.mock import MagicMock

from click.testing import CliRunner

from dagshub.common.cli import cli


def test_create_dataset_cli_invokes_upload_helper(mocker):
    mock_create_dataset = mocker.patch("dagshub.common.cli.create_dataset")
    repo = MagicMock()
    repo.owner = "testuser"
    repo.name = "my-dataset"
    mock_create_dataset.return_value = repo

    with tempfile.TemporaryDirectory() as data_dir:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create_dataset",
                "my-dataset",
                data_dir,
                "--org-name",
                "my-org",
                "--glob-exclude",
                "*.tmp",
                "--private",
            ],
        )

    assert result.exit_code == 0, result.output
    mock_create_dataset.assert_called_once_with(
        "my-dataset",
        data_dir,
        glob_exclude="*.tmp",
        org_name="my-org",
        private=True,
    )


def test_create_dataset_cli_requires_existing_directory():
    runner = CliRunner()
    result = runner.invoke(cli, ["create_dataset", "my-dataset", "nonexistent-directory"])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "invalid value" in result.output.lower()
