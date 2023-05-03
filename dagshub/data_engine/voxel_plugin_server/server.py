import asyncio
import logging
from threading import Thread

from hypercorn.config import Config
from hypercorn.asyncio import serve

from dagshub.data_engine.voxel_plugin_server.app import app

logger = logging.getLogger(__name__)


class PluginServer:
    def __init__(self):
        self._ev_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._ev_loop)
        self._shutdown_event = asyncio.Event()
        self._thread = Thread(target=self._ev_loop.run_until_complete, args=(self.start_serve(),))
        self._thread.start()

    async def start_serve(self):
        cfg = Config()
        # TODO: check for bind
        cfg.bind = "localhost:5152"  # One after the FiftyOne port

        await serve(app, cfg, shutdown_trigger=self._shutdown_event.wait)

    def stop(self):
        self._shutdown_event.set()
        self._thread.join()


def run_plugin_server() -> PluginServer:
    plugin_server = PluginServer()
    return plugin_server
