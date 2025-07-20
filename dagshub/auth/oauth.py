import hashlib
from contextlib import nullcontext
from typing import Optional, NamedTuple
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
        OAuthDagshubToken: The authenticated token object.
    """

    flow_data = oauth_flow_url(host, client_id, referrer)

    webbrowser.open(flow_data.auth_link)

    rich_console.print(
        "[bold]:exclamation::exclamation::exclamation: AUTHORIZATION REQUIRED "
        ":exclamation::exclamation::exclamation:[/bold]",
        justify="center",
    )
    # Doing raw prints here because the rich syntax breaks in colab
    # Printing them line by line, because the link has to be its own print in order for Colab parser to correctly parse
    # the whole link
    print("\n\nOpen the following link in your browser to authorize the client:")
    print(flow_data.auth_link)
    print("\n")

    token = oauth_flow_post(flow_data)
    logger.debug(f"Got token: {token}")
    return token


class OAuthFlowData(NamedTuple):
    """Data object containing all necessary information for OAuth flow."""

    auth_link: str
    """
    The link the user needs to visit to confirm the OAuth flow.
    This link should be shown to the user, who needs to open it in their web browser.
    """
    # Other fields needed to complete the flow in oauth_flow_post
    client_id: str
    oauth_url: str
    middle_man_request_id: str
    state: uuid.UUID


def oauth_flow_url(host: str, client_id: Optional[str], referrer: Optional[str]) -> OAuthFlowData:
    """
    Generate OAuth flow URL and required data for the authentication flow.
    You can use this together with :func:`oauth_flow_post` to complete the full flow manually in custom UIs.

    Args:
        host (str): The URL of the OAuth provider.
        client_id (str): The client ID used for authentication.
        referrer (str): Custom referrer URL, if any.

    Returns:
        OAuthFlowData: Object containing all data needed for the OAuth flow.
    """
    host = host.strip("/")
    oauth_url = urllib.parse.urljoin(host, "login/oauth")
    client_id = client_id or config.client_id
    state = uuid.uuid4()
    middle_man_request_id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    auth_link = (
        f"{oauth_url}/authorize?state={state}&client_id={client_id}&middleman_request_id={middle_man_request_id}"
    )
    if referrer is not None:
        auth_link += f"&referrer={referrer}"

    return OAuthFlowData(
        auth_link=auth_link,
        client_id=client_id,
        oauth_url=oauth_url,
        middle_man_request_id=middle_man_request_id,
        state=state,
    )


def oauth_flow_post(flow_data: OAuthFlowData, quiet: bool = False) -> OAuthDagshubToken:
    """
    Complete the OAuth flow by retrieving an access token (token exchange).
    Blocks until the user completes the flow via the browser, or times out.

    Args:
        flow_data (OAuthFlowData): The flow data containing all required authentication parameters.

    Returns:
        OAuthDagshubToken: The authenticated token.
        :param quiet: Use True to suppress print output
    """
    with rich_console.status("Waiting for authorization") if not quiet else nullcontext():
        res = httpx.post(
            f"{flow_data.oauth_url}/middleman", data={"request_id": flow_data.middle_man_request_id}, timeout=None
        )
    if res.status_code != 200:
        raise Exception(f"Error while getting OAuth code: HTTP {res.status_code}, Body: {res.json()}")
    code = res.json()
    res = httpx.post(
        f"{flow_data.oauth_url}/access_token",
        data={"client_id": flow_data.client_id, "code": code, "state": str(flow_data.state)},
    )
    if res.status_code != 200:
        raise Exception(f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}")
    token = OAuthDagshubToken.deserialize(res.json())
    return token


# TODO: What should this be used for? Not currently raised anywhere
class OauthNonInteractiveShellException(Exception):
    pass
