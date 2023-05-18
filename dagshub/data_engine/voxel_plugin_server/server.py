import asyncio
import logging
from threading import Thread
from typing import TYPE_CHECKING

from hypercorn.config import Config
from hypercorn.asyncio import serve

from dagshub.data_engine.voxel_plugin_server.app import app

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import fiftyone as fo

DEFAULT_PORT = 5152


class PluginServer:
    def __init__(self, voxel_dataset: "fo.Dataset"):
        self._ev_loop = asyncio.new_event_loop()

        self._config = Config()
        self._config.bind = f"localhost:{DEFAULT_PORT}"

        self.set_dataset_config(voxel_dataset)

        asyncio.set_event_loop(self._ev_loop)
        self._shutdown_event = asyncio.Event()
        self._thread = Thread(target=self._ev_loop.run_until_complete, args=(self.start_serve(),))
        self._thread.start()

    @property
    def server_address(self):
        return f"http://{self._config.bind[0]}"

    def set_dataset_config(self, dataset: "fo.Dataset"):
        dataset.app_config.plugins["dagshub"] = {
            "server": self.server_address
        }

    async def start_serve(self):
        await serve(app, self._config, shutdown_trigger=self._shutdown_event.wait)

    def stop(self):
        self._shutdown_event.set()
        self._thread.join()


def run_plugin_server(voxel_dataset: "fo.Dataset") -> PluginServer:
    plugin_server = PluginServer(voxel_dataset)
    return plugin_server
