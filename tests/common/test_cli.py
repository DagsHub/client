from click.testing import CliRunner

from dagshub.common.cli import cli


def _help(*args):
    result = CliRunner().invoke(cli, [*args, "--help"])
    assert result.exit_code == 0, result.output
    return result.output


def test_repo_group_help_lists_a_complete_summary_for_create():
    """
    The command listing used to be built from the first line of the docstring,
    which ended in a colon and read as truncated output.
    """
    output = _help("repo")

    assert "Create a repo, optionally uploading data to it and cloning it" in output
    # The dangling summary the listing used to end on.
    assert "create a repo and optionally:" not in output


def test_repo_create_help_keeps_its_structure():
    """
    The bullet list and the examples are pre-formatted, so click must not
    rewrap them into a single run-on paragraph.
    """
    output = _help("repo", "create")

    assert "- upload files to 'data' from a URL dir using the `-u` flag." in output
    assert "- clone the repo locally using the `--clone` flag." in output
    assert "Example 1:" in output
    assert "Example 2:" in output
    # The rewrapped remnant of the un-escaped bullet.
    assert "are extracted,   other formats" not in output
