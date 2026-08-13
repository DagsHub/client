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


@pytest.mark.parametrize("url", ["https://dagshub.com/", "https://dagshub.com", "my-repo"])
def test_init_from_url_without_owner_and_name_raises(url, mock_get_token):
    """
    A url that carries no owner/name pair should fail loudly instead of
    calling the API with empty segments.
    """
    with pytest.raises(ValueError, match="Could not determine the repo owner and name"):
        dagshub.init(url=url, mlflow=False, dvc=False)
