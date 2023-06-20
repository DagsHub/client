import logging

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from dagshub.data_engine.voxel_plugin_server.routes.label_studio import to_labelstudio
from dagshub.data_engine.voxel_plugin_server.routes.voxel import save_dataset

logger = logging.getLogger(__name__)


async def homepage(request):
    return JSONResponse({"Hello": "from the dagshub voxel dagshub server"})


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
                    Route("/labelstudio/", to_labelstudio, methods=["POST"]),
                    Route("/save_dataset/", save_dataset, methods=["POST"]),
                ])
