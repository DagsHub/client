import contextlib
import os
import httpx


@contextlib.contextmanager
def remember_cwd():
    curdir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(curdir)


def valid_token_side_effect(request: httpx.Request) -> httpx.Response:
    if request.headers["Authorization"] == "Bearer good-token":
        return httpx.Response(
            200,
            json={
                "id": 1,
                "login": "user",
                "full_name": "user",
                "avatar_url": "random_url",
                "username": "user",
            },
        )
    else:
        return httpx.Response(401)
