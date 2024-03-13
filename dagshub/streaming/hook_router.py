from os import PathLike
from typing import Union, Optional

from dagshub.streaming import DagsHubFilesystem


class HookRouter:
    def install_hooks(self, fs: DagsHubFilesystem):
        pass

    def uninstall_hooks(self, fs: Optional[DagsHubFilesystem]=None, path: Optional[Union[str, PathLike]]=None):
        pass
