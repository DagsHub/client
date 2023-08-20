import datetime
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Generator, TYPE_CHECKING

import dateutil.parser
from httpx import Request, Response, Auth

if TYPE_CHECKING:
    from dagshub.auth.tokens import TokenStorage


class DagshubAuthenticator(Auth):
    """
    This class contains a token + flow on how to re-init the token in case of failure
    """

    def __init__(self, token: "DagshubTokenABC", token_storage: "TokenStorage"):
        self.token = token
        self.token_storage = token_storage

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        # TODO: failure mode recovery
        yield self.token(request)


class TokenDeserializationError(Exception):
    ...


class DagshubTokenABC(metaclass=ABCMeta):
    token_type = "NONE"

    def __call__(self, request: Request) -> Request:
        request.headers["Authorization"] = f"Bearer {self.token_text}"
        return request

    @staticmethod
    @abstractmethod
    def deserialize(values: Dict[str, Any]):
        ...

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def token_text(self) -> str:
        ...

    @property
    @abstractmethod
    def is_expired(self) -> bool:
        ...


class OauthDagshubToken(DagshubTokenABC):
    token_type = "bearer"

    def __init__(self, token_value: str, expiry_date: datetime.datetime):
        self.token_value = token_value
        self.expiry_date = expiry_date

    def serialize(self) -> Dict[str, Any]:
        return {
            "access_token": self.token_value,
            "expiry": self.expiry_date.isoformat(),
            "token_type": self.token_type,
        }

    @staticmethod
    def deserialize(values: Dict[str, Any]):
        token_value = values["access_token"]
        expiry_date = values["expiry"]
        expiry_date = dateutil.parser.parse(expiry_date)
        return OauthDagshubToken(token_value, expiry_date)

    @property
    def token_text(self) -> str:
        return self.token_value

    @property
    def is_expired(self) -> bool:
        return self.expiry_date < datetime.datetime.now(tz=self.expiry_date.tzinfo)

    def __repr__(self):
        return f"Dagshub OAuth token, valid until {self.expiry_date}"


class AppDagshubToken(DagshubTokenABC):
    token_type = "app-token"

    def __init__(self, token_value: str):
        self.token_value = token_value

    def serialize(self) -> Dict[str, Any]:
        return {
            "access_token": self.token_value,
            "expiry": "never",
            "token_type": self.token_type,
        }

    @staticmethod
    def deserialize(values: Dict[str, Any]):
        return AppDagshubToken(values["access_token"])

    @property
    def token_text(self) -> str:
        return self.token_value

    @property
    def is_expired(self) -> bool:
        return False

    def __repr__(self):
        return "Dagshub App token"


class HTTPBearerAuth(Auth):
    """Attaches HTTP Bearer Authorization to the given Request object."""

    def __init__(self, token):
        self.token = token

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

    def __eq__(self, other):
        return all([
            self.token == getattr(other, 'token', None),
        ])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r
