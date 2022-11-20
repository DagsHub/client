import os
import pytest

import dagshub


@pytest.fixture(autouse=True)
def mock_env_vars():
    # Skip auth
    os.environ["DAGSHUB_USER_TOKEN"] = "token"


@pytest.fixture
def repo_with_hooks(dagshub_repo):
    dagshub.streaming.install_hooks()
    yield dagshub_repo
    dagshub.streaming.uninstall_hooks()
