import hashlib
from typing import Optional, Dict
import logging
import urllib
import uuid
import httpx
from dagshub.common import config

logger = logging.getLogger(__name__)


def oauth_flow(
    host: str,
    client_id: Optional[str] = None
) -> Dict:

    host = host.strip("/")
    dagshub_url = urllib.parse.urljoin(host, "login/oauth")
    client_id = client_id or config.client_id
    state = uuid.uuid4()
    middle_man_request_id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()

    link_prompt = f"Go to {dagshub_url}/authorize?state={state}&client_id={client_id}" \
                  f"&middleman_request_id={middle_man_request_id} to authorize the client."
    print(link_prompt)

    res = httpx.post(
        f"{dagshub_url}/middleman",
        data={"request_id": middle_man_request_id}, timeout=None
    )

    if res.status_code != 200:
        raise Exception(
            f"Error while getting OAuth code: HTTP {res.status_code}, Body: {res.json()}"
        )
    code = res.json()

    res = httpx.post(
        f"{dagshub_url}/access_token",
        data={"client_id": client_id, "code": code, "state": str(state)}
    )

    if res.status_code != 200:
        raise Exception(
            f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}"
        )
    token = res.json()

    logger.debug(f"Got token: {token}")
    return token


class OauthNonInteractiveShellException(Exception):
    pass
