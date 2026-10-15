import os
from unittest.mock import MagicMock

import pytest

import dagshub
from dagshub.common.api.repo import RepoNotFoundError


@pytest.fixture
def mock_repo_api(mocker):
    mock = mocker.patch("dagshub.common.init.RepoAPI")
    mock.return_value.get_repo_info.side_effect = RepoNotFoundError()
    return mock


@pytest.fixture
def mock_user_api(mocker):
    user = MagicMock()
    user.username = "testuser"
    mock = mocker.patch("dagshub.common.init.UserAPI")
    mock.get_current_user.return_value = user
    mock.get_user_from_token.return_value = user
    return mock


@pytest.fixture
def mock_create_repo(mocker):
    return mocker.patch("dagshub.common.init.create_repo")


@pytest.fixture
def mock_get_token(mocker):
    return mocker.patch("dagshub.common.init.get_token", return_value="fake-token")


@pytest.fixture
def mock_log_message(mocker):
    return mocker.patch("dagshub.common.init.log_message")


def test_init_creates_repo_under_org_when_owner_differs(
    mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    dagshub.init(repo_owner="my-org", repo_name="my-repo", mlflow=False, dvc=False)

    mock_user_api.get_current_user.assert_called_once()
    mock_create_repo.assert_called_once_with("my-repo", org_name="my-org", host="https://dagshub.com")
    mock_log_message.assert_any_call(
        'Repository my-repo doesn\'t exist, creating it under organization "my-org".'
    )


def test_init_creates_repo_under_current_user_when_owner_matches(
    mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    dagshub.init(repo_owner="testuser", repo_name="my-repo", mlflow=False, dvc=False)

    mock_user_api.get_current_user.assert_called_once()
    mock_create_repo.assert_called_once_with("my-repo", host="https://dagshub.com")
    mock_log_message.assert_any_call(
        "Repository my-repo doesn't exist, creating it under current user."
    )


def test_init_creates_repo_under_current_user_from_url(
    mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    dagshub.init(url="https://dagshub.com/testuser/my-repo", mlflow=False, dvc=False)

    mock_user_api.get_current_user.assert_called_once()
    mock_create_repo.assert_called_once_with("my-repo", host="https://dagshub.com")
    mock_log_message.assert_any_call(
        "Repository my-repo doesn't exist, creating it under current user."
    )


def test_init_creates_repo_under_org_from_url(
    mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    dagshub.init(url="https://dagshub.com/my-org/my-repo", mlflow=False, dvc=False)

    mock_user_api.get_current_user.assert_called_once()
    mock_create_repo.assert_called_once_with("my-repo", org_name="my-org", host="https://dagshub.com")
    mock_log_message.assert_any_call(
        'Repository my-repo doesn\'t exist, creating it under organization "my-org".'
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://dagshub.com/my-org/my-repo/",
        "https://dagshub.com/my-org/my-repo.git/",
        "https://dagshub.com/my-org/my-repo///",
    ],
)
def test_init_from_url_tolerates_trailing_slash(
    url, mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    """
    A url copied from the browser address bar carries a trailing slash, which
    used to shift every segment by one and yield repo_owner="my-repo" with an
    empty repo_name.
    """
    dagshub.init(url=url, mlflow=False, dvc=False)

    mock_repo_api.assert_called_once_with("my-org/my-repo", host="https://dagshub.com")
    mock_create_repo.assert_called_once_with("my-repo", org_name="my-org", host="https://dagshub.com")


@pytest.mark.parametrize(
    "url",
    [
        "https://dagshub.com/",
        "https://dagshub.com",
        "my-repo",
        # One path segment only: the last two slash-separated pieces are
        # "dagshub.com" and "my-repo", which looks like owner/name and is not.
        "https://dagshub.com/my-repo",
        "https://dagshub.com/my-repo/",
    ],
)
def test_init_from_url_without_owner_and_name_raises(url, mock_get_token):
    """
    A url that carries no owner/name pair should fail loudly instead of
    calling the API with empty segments.
    """
    with pytest.raises(ValueError, match="Could not determine the repo owner and name"):
        dagshub.init(url=url, mlflow=False, dvc=False)


@pytest.fixture
def clean_environ(mocker):
    """Let the test read what init() wrote to os.environ, then put it back."""
    return mocker.patch.dict(os.environ, {}, clear=False)


@pytest.mark.parametrize(
    "url",
    [
        "https://dagshub.com/my-org//my-repo",
        "https://dagshub.com//my-org/my-repo/",
        "https://dagshub.com/my-org/my-repo.git",
    ],
)
def test_init_hands_a_canonical_url_to_mlflow(
    url, clean_environ, mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    """
    Empty path segments are skipped when reading the owner and name, so they
    must be skipped in the url too - otherwise the API is called with
    "my-org/my-repo" while MLflow is pointed at ".../my-org//my-repo.mlflow".
    """
    dagshub.init(url=url, mlflow=True, dvc=False)

    mock_repo_api.assert_called_once_with("my-org/my-repo", host="https://dagshub.com")
    assert os.environ["MLFLOW_TRACKING_URI"] == "https://dagshub.com/my-org/my-repo.mlflow"


def test_init_does_not_leak_url_credentials_to_mlflow(
    clean_environ, mock_repo_api, mock_user_api, mock_create_repo, mock_get_token, mock_log_message
):
    """
    A token pasted into the url must not travel on into the tracking URI - the
    same url is also written to .dvc/config, which is committed.
    """
    dagshub.init(url="https://user:s3cret-token@dagshub.com/my-org/my-repo", mlflow=True, dvc=False)

    assert os.environ["MLFLOW_TRACKING_URI"] == "https://dagshub.com/my-org/my-repo.mlflow"
    assert "s3cret-token" not in os.environ["MLFLOW_TRACKING_URI"]


def test_init_does_not_leak_url_credentials_in_the_error_message(mock_get_token):
    """
    The url is quoted back when it cannot be parsed, and that message is likely
    to be logged, so it must not carry the userinfo it was given.
    """
    with pytest.raises(ValueError) as excinfo:
        dagshub.init(url="https://user:s3cret-token@dagshub.com/my-repo", mlflow=False, dvc=False)

    assert "s3cret-token" not in str(excinfo.value)
    assert "user:" not in str(excinfo.value)
