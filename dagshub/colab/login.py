from dagshub.auth import add_oauth_token, get_token
from dagshub.common.api import RepoAPI, UserAPI
from dagshub.common.api.repo import RepoNotFoundError
from dagshub.upload import create_repo

COLAB_REPO_NAME = "dagshub-drive"


def login() -> str:
    """
    Run custom colab-specific flow, which helps with setting up a repository,
    storage of which will be used as an alternative to Google Drive.

    Returns the name of the repository that can be used with colab-related functionality (``<user>/dagshub-drive``)
    """
    try:
        token = get_token(fail_if_no_token=True)
    except RuntimeError:
        add_oauth_token(referrer="colab")
        token = get_token()

    username = UserAPI.get_user_from_token(token).username

    colab_repo = RepoAPI(f"{username}/{COLAB_REPO_NAME}")
    try:
        colab_repo.get_repo_info()
    except RepoNotFoundError:
        create_repo(COLAB_REPO_NAME)
    print(f"Repository {colab_repo.full_name} is ready for use with Colab. Link to the repository:")
    print(colab_repo.repo_url)
    return colab_repo.full_name
