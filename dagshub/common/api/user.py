from functools import cached_property, lru_cache
from typing import Optional, Any, Union

import dacite

from dagshub.auth import get_authenticator, get_token
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.common.api.responses import UserAPIResponse
from dagshub.common.helpers import http_request
from dagshub.common.util import multi_urljoin


class UserNotFoundError(Exception):
    pass


class UserAPI:
    def __init__(self, user: Union[str, UserAPIResponse], host: Optional[str] = None, auth: Optional[Any] = None):
        self._user_info: Optional[UserAPIResponse] = None
        if isinstance(user, UserAPIResponse):
            self._user_info = user
            self._username = user.username
        else:
            self._username = user
        self.host = host if host is not None else config.host

        if auth is None:
            self.auth = get_authenticator(host=host)
        else:
            self.auth = auth

    @staticmethod
    def get_user_from_token(token_or_authenticator: Union[str, Any], host: Optional[str] = None) -> "UserAPI":
        if host is None:
            host = config.host
        user_url = multi_urljoin(host, "api/v1/user")
        if isinstance(token_or_authenticator, str):
            auth = HTTPBearerAuth(token_or_authenticator)
        else:
            auth = token_or_authenticator
        resp = http_request("GET", user_url, auth=auth)
        if resp.status_code == 404:
            raise UserNotFoundError
        if resp.status_code != 200:
            raise RuntimeError(f"Got HTTP status {resp.status_code} while trying to get user: {resp.content}")
        user_info = dacite.from_dict(UserAPIResponse, resp.json())
        return UserAPI(user=user_info, host=host, auth=auth)

    @staticmethod
    @lru_cache
    def get_current_user(host: Optional[str] = None) -> "UserAPI":
        return UserAPI.get_user_from_token(get_token(host=host), host=host)

    @property
    def username(self) -> str:
        return self.user_info.username

    @property
    def user_id(self) -> int:
        return self.user_info.id

    @cached_property
    def user_info(self) -> UserAPIResponse:
        if self._user_info is not None:
            return self._user_info
        user_url = multi_urljoin(self.host, "api/v1/users", self._username)
        resp = http_request("GET", user_url, auth=self.auth)
        if resp.status_code == 404:
            raise UserNotFoundError
        if resp.status_code != 200:
            raise RuntimeError(
                f"Got HTTP status {resp.status_code} while trying to get user {self._username}: {resp.content}"
            )
        user_info = dacite.from_dict(UserAPIResponse, resp.json())
        return user_info
