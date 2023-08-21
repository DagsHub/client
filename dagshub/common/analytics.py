from threading import Thread
from typing import Dict, Any, Optional, Union

from dagshub.auth import get_token
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.common.api.repo import RepoAPI
from dagshub.common.helpers import http_request


def send_analytics_event(event_name: str, repo: Optional[Union[int, "RepoAPI"]] = None, **event_data: Dict[str, Any]):
    if config.disable_analytics:
        return
    if event_data is None:
        event_data = {}
    event_data["event"] = event_name
    if repo is not None:
        if type(repo) is int:
            event_data["repo_id"] = repo
        else:
            event_data["repo_id"] = repo.id
    host = config.host
    token = get_token(host=host)
    t = Thread(target=_send, args=(event_data, host, token), daemon=True)
    t.start()


def _send(event_data: Dict[str, Any], host: str, token: str):
    url = f"{host}/api/internal/trackAnalyticsEvent"

    http_request("POST", url, data=event_data, auth=HTTPBearerAuth(token))
