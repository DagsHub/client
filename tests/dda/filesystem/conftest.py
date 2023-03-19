import pytest
from dagshub.streaming import install_hooks, uninstall_hooks


@pytest.fixture
def repo_with_hooks(dagshub_repo):
    install_hooks()
    yield dagshub_repo
    uninstall_hooks()
