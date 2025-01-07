from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from json import JSONDecodeError
from typing import Optional
import importlib.util
import semver

from dagshub.common.api.repo import RepoAPI
from dagshub.auth import get_token
from dagshub.common import config


def _use_legacy_client():
    """
    https://github.com/HumanSignal/label-studio/releases/tag/1.13.0, \
            https://github.com/HumanSignal/label-studio/pull/5961; \
            introduces breaking changes; anyone using SDK < 1.0 should use the legacy client.
    :meta experimental:
    """
    import label_studio_sdk

    return semver.compare("1.0.0", label_studio_sdk.__version__) == 1


@retry(retry=retry_if_exception_type(JSONDecodeError), wait=wait_fixed(3), stop=stop_after_attempt(5))
def get_label_studio_client(
    repo: str, legacy_client: Optional[bool] = None, host: Optional[str] = None, token: Optional[str] = None
):
    """
    Creates a
    `label_studio_sdk.client.LabelStudio <https://api.labelstud.io/api-reference/introduction/getting-started>`_ /
    `label_studio_sdk.Client (legacy) <https://labelstud.io/guide/sdk>`_
    object to interact with the LabelStudio instance associated with the repository.

    Args:
        repo: Name of the repo in the format of ``username/reponame``
        legacy_client: if True, returns the older legacy LabelStudio Client.
        host: URL of the hosted DagsHub instance. default is ``https://dagshub.com``.
        token: (optional, default: None) use this token for LS requests. By default, will use current user's token.

    Returns:
        `label_studio_sdk.Client` / `label_studio_sdk.client.LabelStudio` object
    """

    if importlib.util.find_spec("label_studio_sdk") is None:
        raise ModuleNotFoundError("Could not import module label_studio_sdk. Make sure to pip install label_studio_sdk")

    if legacy_client is None:
        legacy_client = _use_legacy_client()

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
