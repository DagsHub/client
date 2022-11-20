import pytest
import dagshub


@pytest.fixture
def repo_with_hooks(dagshub_repo):
    dagshub.streaming.install_hooks()
    yield dagshub_repo
    dagshub.streaming.uninstall_hooks()
