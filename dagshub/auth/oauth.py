from typing import Optional, Dict
import logging
import requests
import urllib
import uuid
from dagshub.common import config
import concurrent.futures
# import getpass
# import sys
# import pytimedinput

# CODE_INPUT_TIMEOUT = 60
logger = logging.getLogger(__name__)


def call_middleman(dagshub_url, middle_man_uuid):
    res = requests.post(
        f"{dagshub_url}/middleman",
        data={"uuid": middle_man_uuid},
    )
    return res


def oauth_flow(
    host: str,
    client_id: Optional[str] = None
) -> Dict:

    host = host.strip("/")
    dagshub_url = urllib.parse.urljoin(host, "login/oauth")
    client_id = client_id or config.client_id
    state = uuid.uuid4()
    middle_man_uuid = uuid.uuid4()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(call_middleman, dagshub_url, middle_man_uuid)
        link_prompt = f"Go to {dagshub_url}/authorize?state={state}&client_id={client_id}" \
                      f"&middleman_uuid={middle_man_uuid} to authorize the client."
        print(link_prompt)
        res = future.result()

    if res.status_code != 200:
        # maybe add a different error for the timeout flow
        raise Exception(
            f"Error while getting OAuth code: HTTP {res.status_code}, Body: {res.json()}"
        )
    code = res.json()["Code"]
    print(code)

    res = requests.post(
        f"{dagshub_url}/access_token",
        data={"client_id": client_id, "code": code, "state": state},
    )
    if res.status_code != 200:
        raise Exception(
            f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}"
        )
    token = res.json()

    logger.debug(f"Got token: {token}")
    # Guy- should we print so massage to let the user know he is now logged in?
    return token

# Guy- should we leave both or delete the old one? currently i commented it out

# def oauth_flow(
#     host: str,
#     client_id: Optional[str] = None,
#     code_input_timeout: Optional[int] = None,
# ) -> Dict:
#     client_id = client_id or config.client_id
#     if code_input_timeout is None:
#         code_input_timeout = CODE_INPUT_TIMEOUT
#     state = uuid.uuid4()
#     host = host.strip("/")
#     dagshub_url = urllib.parse.urljoin(host, "login/oauth")
#     link_prompt = f"Go to {dagshub_url}/authorize?state={state}&client_id={client_id} and paste the code back in here"
#     code_prompt = "Code:"
#     if code_input_timeout <= 0:
#         print(link_prompt)
#         code = getpass.getpass(code_prompt)
#     else:
#         if not sys.__stdin__.isatty():
#             raise OauthNonInteractiveShellException(
#                 "Can't perform OAuth in a non-interactive shell. "
#                 "Please get a token using this command in a shell: dagshub login"
#             )
#         print(link_prompt)
#         code, timed_out = pytimedinput.timedInput(
#             prompt=code_prompt, timeout=code_input_timeout
#         )
#         if timed_out:
#             raise RuntimeError("Timed out input of OAuth code")
#     res = requests.post(
#         f"{dagshub_url}/access_token",
#         data={"client_id": client_id, "code": code, "state": state},
#     )
#     if res.status_code != 200:
#         raise Exception(
#             f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}"
#         )
#     token = res.json()
#     logger.debug(f"Got token: {token}")
#     return token


class OauthNonInteractiveShellException(Exception):
    pass
