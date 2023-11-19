import asyncio
import logging
from threading import Thread
from typing import TYPE_CHECKING, Optional

from hypercorn.asyncio import serve
from hypercorn.config import Config

from dagshub.common import is_inside_colab
from dagshub.data_engine.voxel_plugin_server.app import app
from dagshub.data_engine.voxel_plugin_server.models import PluginServerState

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dagshub.data_engine.model.datasource import Datasource
    import fiftyone as fo

DEFAULT_PORT = 5152

_running_server = None


class PluginServer:
    def __init__(self, state: PluginServerState):
        self._ev_loop = asyncio.new_event_loop()

        self._config = Config()
        self._config.bind = [f"localhost:{DEFAULT_PORT}"]
        self._state = state

        self.set_dataset_config(self._state.voxel_session)

        asyncio.set_event_loop(self._ev_loop)
        self._shutdown_event = asyncio.Event()
        self._thread = Thread(target=self._ev_loop.run_until_complete, args=(self.start_serve(),), daemon=True)
        self._thread.start()

    @property
    def server_address(self):
        return f"http://{self._config.bind[0]}"

    def set_dataset_config(self, session: "fo.Session"):
        session.config.plugins["dagshub"] = {
            "server": self.server_address,
            "in_colab": is_inside_colab(),
            "datasource_name": self._state.datasource.source.name,
        }
        session.refresh()

    async def start_serve(self):
        self.set_state(self._state)
        await serve(app, self._config, shutdown_trigger=self._shutdown_event.wait)

    def set_state(self, state: PluginServerState):
        self._state = state
        app.state.PLUGIN_STATE = self._state

    def stop(self):
        self._shutdown_event.set()
        self._thread.join()


def run_plugin_server(voxel_session: "fo.Session", datasource: "Datasource", branch: Optional[str]) -> PluginServer:
    global _running_server
    state = PluginServerState(voxel_session, datasource, branch)
    if _running_server is None:
        _running_server = PluginServer(state)
    else:
        _running_server.set_state(state)

    return _running_server
