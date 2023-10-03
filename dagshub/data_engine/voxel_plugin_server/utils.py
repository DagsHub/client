import os
import shutil
import sys
from typing import TYPE_CHECKING

from dagshub.common.helpers import prompt_user

if TYPE_CHECKING:
    from starlette.requests import Request
    from dagshub.data_engine.voxel_plugin_server.models import PluginServerState


def set_voxel_envvars():
    """
    Sets the environment variables relevant for voxel:
        FIFTYONE_PLUGINS_DIR - where to load the plugins from
    """
    script_dir = os.path.dirname(__file__)
    plugin_dir = os.environ.get("DAGSHUB_FIFTYONE_PLUGINS_DIR", os.path.join(script_dir, "plugins"))
    plugin_dir = os.path.abspath(plugin_dir)
    fo_dir_envkey = "FIFTYONE_PLUGINS_DIR"
    if fo_dir_envkey in os.environ and os.environ[fo_dir_envkey] != plugin_dir:
        plugins_dest_dir = os.path.join(os.environ[fo_dir_envkey], "dagshub")
        # TODO: handle version changes, for now prompt only if the plugin isn't copied
        if not os.path.exists(plugins_dest_dir):
            response = prompt_user(
                f"You have {fo_dir_envkey} env var setup to {os.environ[fo_dir_envkey]}. "
                "Do you want to copy the dagshub plugin there?"
                "You need the plugin copied in order to get full integration experience",
                default=True,
            )
            if not response:
                return
            shutil.copytree(os.path.join(plugin_dir, "dagshub"), plugins_dest_dir)
    else:
        os.environ[fo_dir_envkey] = plugin_dir

    # Reset the plugin dir if voxel has already been imported
    if "fiftyone" in sys.modules:
        import fiftyone as fo

        fo.config.plugins_dir = plugin_dir


def get_plugin_state(request: "Request") -> "PluginServerState":
    return request.app.state.PLUGIN_STATE
