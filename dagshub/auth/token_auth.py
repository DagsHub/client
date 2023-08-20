from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Generator, TYPE_CHECKING

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


class DagshubTokenABC(metaclass=ABCMeta):
    token_type = "NONE"

    def __call__(self, request: Request) -> Request:
        request.headers["Authorization"] = f"Bearer {self.token_text}"
        return request

    @abstractmethod
    def deserialize(self, values: Dict[str, Any]):
        ...

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    @property
    def token_text(self) -> str:
        ...


class OauthDagshubToken(DagshubTokenABC):
    token_type = "bearer"

    def serialize(self) -> Dict[str, Any]:
        raise NotImplementedError

    def deserialize(self, values: Dict[str, Any]):
        raise NotImplementedError

    @property
    def token_text(self) -> str:
        raise NotImplementedError


class AppDagshubToken(DagshubTokenABC):
    token_type = "app-token"

    def serialize(self) -> Dict[str, Any]:
        raise NotImplementedError

    def deserialize(self, values: Dict[str, Any]):
        raise NotImplementedError

    @property
    def token_text(self) -> str:
        raise NotImplementedError


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
