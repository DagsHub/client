from requests.auth import AuthBase


class HTTPBearerAuth(AuthBase):
    """Attaches HTTP Bearer Authorization to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return all([
            self.token == getattr(other, 'token', None),
            ])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r
