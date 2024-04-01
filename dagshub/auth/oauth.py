import hashlib
from typing import Optional
import logging
import urllib
import uuid
import httpx
import webbrowser

from dagshub.auth.token_auth import OAuthDagshubToken
from dagshub.common import config, rich_console

logger = logging.getLogger(__name__)


def oauth_flow(host: str, client_id: Optional[str] = None, referrer: Optional[str] = None) -> OAuthDagshubToken:
    """
    Initiate the OAuth 2.0 flow for obtaining an access token.

    Args:
        host (str): The URL of the OAuth provider.
        client_id (Optional[str], optional): The client ID used for authentication.
            If not provided, it will use the default client ID from the configuration.
        referrer (Optional[str], optional): For custom referral

    Returns:
        Dict: A dictionary containing the obtained access token.
    """

    host = host.strip("/")
    dagshub_url = urllib.parse.urljoin(host, "login/oauth")
    client_id = client_id or config.client_id
    state = uuid.uuid4()
    middle_man_request_id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    auth_link = (
        f"{dagshub_url}/authorize?state={state}&client_id={client_id}&middleman_request_id={middle_man_request_id}"
    )
    if referrer is not None:
        auth_link += f"&referrer={referrer}"

    webbrowser.open(auth_link)

    rich_console.print(
        "[bold]:exclamation::exclamation::exclamation: AUTHORIZATION REQUIRED "
        ":exclamation::exclamation::exclamation:[/bold]",
        justify="center",
    )
    # Doing raw prints here because the rich syntax breaks in colab
    # Printing them line by line, because the link has to be its own print in order for Colab parser to correctly parse
    # the whole link
    print("\n\nOpen the following link in your browser to authorize the client:")
    print(auth_link)
    print("\n")

    with rich_console.status("Waiting for authorization"):
        res = httpx.post(f"{dagshub_url}/middleman", data={"request_id": middle_man_request_id}, timeout=None)

    if res.status_code != 200:
        raise Exception(f"Error while getting OAuth code: HTTP {res.status_code}, Body: {res.json()}")
    code = res.json()

    res = httpx.post(f"{dagshub_url}/access_token", data={"client_id": client_id, "code": code, "state": str(state)})

    if res.status_code != 200:
        raise Exception(f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}")
    token = OAuthDagshubToken.deserialize(res.json())

    logger.debug(f"Got token: {token}")
    return token


class OauthNonInteractiveShellException(Exception):
    pass
