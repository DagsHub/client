import logging

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


async def homepage(request):
    return JSONResponse({"Hello": "from the dagshub voxel plugin server"})


async def to_labelstudio(request: Request):
    logger.info(await request.json())
    return JSONResponse("Hi!!")


app = Starlette(debug=True,
                middleware=[
                    Middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_methods=["*"],
                    ),
                ],
                routes=[
                    Route("/", homepage),
                    Route("/labelstudio", to_labelstudio, methods=["POST"])
                ])
