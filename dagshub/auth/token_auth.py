import typing
from httpx import Request, Response, Auth


class HTTPBearerAuth(Auth):
    """Attaches HTTP Bearer Authorization to the given Request object."""

    def __init__(self, token):
        self.token = token

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
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
