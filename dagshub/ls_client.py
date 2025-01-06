from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from json import JSONDecodeError
from typing import Optional
import importlib.util

from dagshub.common.api.repo import RepoAPI
from dagshub.auth import get_token
from dagshub.common import config


@retry(retry=retry_if_exception_type(JSONDecodeError), wait=wait_fixed(3), stop=stop_after_attempt(5))
def get_label_studio_client(
    repo: str, legacy_client: bool = False, host: Optional[str] = None, token: Optional[str] = None
):
    """
    Creates a `label_studio_sdk.Client / label_studio_sdk.client.LabelStudio \
            <https://labelstud.io/guide/sdk>`.\
    object to interact with the label studio instance associated with the repository.

    Args:
        repo: Name of the repo in the format of ``username/reponame``
        legacy_client: if True, returns the older legacy LabelStudio Client.
        host: URL of the hosted DagsHub instance. default is ``https://dagshub.com``.
        token: (optional, default: None) uses programmatically specified token, \
                if not provided either uses cached token or requests oauth interactively.

    Returns:
        `label_studio_sdk.Client` / `label_studio_sdk.client.LabelStudio` object
    """

    if importlib.util.find_spec("label_studio_sdk") is None:
        raise ModuleNotFoundError("Could not import module label_studio_sdk. Make sure to pip install label_studio_sdk")
    if not host:
        host = config.host
    if legacy_client:
        from label_studio_sdk import Client as LabelStudio
    else:
        from label_studio_sdk.client import LabelStudio

    repo_api = RepoAPI(repo, host=host)
    kwargs = {
        "url" if legacy_client else "base_url": repo_api.label_studio_api_url()[:-4],
        "api_key": token if token is not None else get_token(host=host),
    }

    return LabelStudio(**kwargs)
