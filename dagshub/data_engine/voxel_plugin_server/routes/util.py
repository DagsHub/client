import traceback
from functools import wraps

from starlette.responses import Response


def error_handler(route):
    """
    Required in order to not break CORS.
    Starlette's CORS middleware is applied only after its default error handler
    This means that any exception ends up being blocked as a request on voxel's side
    """

    @wraps(route)
    async def wrapped(*args, **kwargs):
        try:
            return await route(*args, **kwargs)
        except:  # noqa
            traceback.print_exc()
            return Response(traceback.format_exc(), status_code=500)

    return wrapped
