import getpass
import sys
from typing import Optional, Dict
import logging

import pytimedinput
import urllib
import uuid
from dagshub.common import config
from dagshub.common.helpers import http_request

CODE_INPUT_TIMEOUT = 60

logger = logging.getLogger(__name__)


def oauth_flow(
    host: str,
    client_id: Optional[str] = None,
    code_input_timeout: Optional[int] = None,
) -> Dict:
    client_id = client_id or config.client_id
    if code_input_timeout is None:
        code_input_timeout = CODE_INPUT_TIMEOUT
    state = uuid.uuid4()
    host = host.strip("/")
    dagshub_url = urllib.parse.urljoin(host, "login/oauth")
    link_prompt = f"Go to {dagshub_url}/authorize?state={state}&client_id={client_id} and paste the code back in here."
    code_prompt = "Code:"
    if code_input_timeout <= 0:
        print(link_prompt)
        code = getpass.getpass(code_prompt)
    else:
        if not sys.__stdin__.isatty():
            raise OauthNonInteractiveShellException(
                "Can't perform OAuth in a non-interactive shell. "
                "Please get a token using this command in a shell: dagshub login"
            )
        print(link_prompt)
        code, timed_out = pytimedinput.timedInput(
            prompt=code_prompt, timeout=code_input_timeout
        )
        if timed_out:
            raise RuntimeError("Timed out input of OAuth code")
    res = http_request(
        "POST",
        f"{dagshub_url}/access_token",
        data={"client_id": client_id, "code": code, "state": state},
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
