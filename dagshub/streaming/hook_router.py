import builtins
import importlib
import io
import logging
import os
import sys
from os import PathLike
from typing import Union, Optional, Callable, Dict, List, TYPE_CHECKING, Set

from dagshub.common import is_inside_notebook, is_inside_colab
from dagshub.streaming.dataclasses import DagshubPath, PathType
from dagshub.streaming.errors import FilesystemAlreadyMountedError
from dagshub.streaming.filesystem import DagshubScandirIterator
from dagshub.streaming.util import wrapreturn

from pathlib import Path

if TYPE_CHECKING:
    from dagshub.streaming.filesystem import DagsHubFilesystem

# Pre 3.11 - need to patch _NormalAccessor for _pathlib, because it pre-caches open and other functions.
# In 3.11 _NormalAccessor was removed
PRE_PYTHON3_11 = sys.version_info.major == 3 and sys.version_info.minor < 11
if PRE_PYTHON3_11:
    from pathlib import _NormalAccessor as _pathlib  # noqa

logger = logging.getLogger(__name__)


class HookRouter:
    original_open = builtins.open
    original_stat = os.stat
    original_listdir = os.listdir
    original_scandir = os.scandir
    original_chdir = os.chdir

    unpatched: Dict[str, Callable] = {}

    is_monkey_patching = False

    active_filesystems: Set["DagsHubFilesystem"] = set()

    # Framework-specific override functions.
    # These functions will be patched with a function that calls fs.open() before calling the original function
    # Classes are marked by $, so if you need to change a static/class method, use module.$class.func
    _framework_override_map: Dict[str, List[str]] = {
        "transformers": ["safetensors.safe_open", "tokenizers.$Tokenizer.from_file"],
    }

    @classmethod
    def open(
        cls,
        file: PathType,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        if isinstance(file, int):
            return cls.original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
        dh_path = cls.determine_fs(file)
        if dh_path is not None:
            return dh_path.fs.open(dh_path, mode, buffering, encoding, errors, newline, closefd, opener)
        else:
            return cls.original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    @classmethod
    def stat(cls, path: PathType, *args, dir_fd=None, follow_symlinks=True):
        if isinstance(path, int):
            return cls.original_stat(path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        dh_path = cls.determine_fs(path)
        if dh_path is not None:
            return dh_path.fs.stat(dh_path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        else:
            return cls.original_stat(path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    @classmethod
    def listdir(cls, path: PathType = "."):
        if isinstance(path, int):
            return cls.original_listdir(path)
        dh_path = cls.determine_fs(path)
        if dh_path is not None:
            return dh_path.fs.listdir(dh_path)
        else:
            return cls.original_listdir(path)

    @classmethod
    @wrapreturn(DagshubScandirIterator)
    def scandir(cls, path: PathType = "."):
        if isinstance(path, int):
            return cls.original_scandir(path)
        dh_path = cls.determine_fs(path)
        if dh_path is not None:
            return dh_path.fs.scandir(path)
        else:
            return cls.original_scandir(path)

    @classmethod
    def chdir(cls, path: PathType):
        if isinstance(path, int):
            return cls.original_chdir(path)
        dh_path = cls.determine_fs(path)
        if dh_path is not None:
            return dh_path.fs.chdir(dh_path)
        else:
            return cls.original_chdir(path)

    @classmethod
    def os_open(cls, path: Union[str, bytes, PathLike], flags, mode=0o777, *args, dir_fd=None):
        dh_path = cls.determine_fs(path)
        if dh_path is not None:
            return dh_path.fs.os_open(dh_path, flags, mode, *args, dir_fd=dir_fd)
        else:
            return os.open(path, flags, mode, *args, dir_fd=dir_fd)

    @classmethod
    def init_monkey_patch(cls, frameworks: Optional[List[str]] = None):
        if cls.is_monkey_patching:
            return
        # Save the current unpatched functions
        cls.unpatched = {
            "open": cls.original_open,
            "stat": cls.original_stat,
            "listdir": cls.original_listdir,
            "scandir": cls.original_scandir,
            "chdir": cls.original_chdir,
        }
        if PRE_PYTHON3_11:
            cls.unpatched["pathlib_open"] = _pathlib.open

        # IPython patches io.open to its own override, so we need to overwrite that also
        # More at _modified_open function in IPython sources:
        # https://github.com/ipython/ipython/blob/main/IPython/core/interactiveshell.py
        if is_inside_notebook() and not is_inside_colab():
            import IPython.core.interactiveshell

            instance = IPython.core.interactiveshell.InteractiveShell._instance  # noqa
            if instance is not None and hasattr(instance, "user_ns") and "open" in instance.user_ns:
                cls.unpatched["notebook_open"] = instance.user_ns["open"]
                instance.user_ns["open"] = cls.open

        io.open = builtins.open = cls.open
        os.stat = cls.stat
        os.listdir = cls.listdir
        os.scandir = cls.scandir
        os.chdir = cls.chdir
        if PRE_PYTHON3_11:
            if sys.version_info.minor == 10:
                # Python 3.10 - pathlib uses io.open
                _pathlib.open = cls.open
            else:
                # Python <=3.9 - pathlib uses os.open
                _pathlib.open = cls.os_open
            _pathlib.stat = cls.stat
            _pathlib.listdir = cls.listdir
            _pathlib.scandir = cls.scandir

        cls._install_framework_hooks(frameworks)
        cls.is_monkey_patching = True

    @classmethod
    def uninstall_monkey_patch(cls):
        if not cls.is_monkey_patching:
            return
        io.open = builtins.open = cls.unpatched["open"]
        os.stat = cls.unpatched["stat"]
        os.listdir = cls.unpatched["listdir"]
        os.scandir = cls.unpatched["scandir"]
        os.chdir = cls.unpatched["chdir"]
        if PRE_PYTHON3_11:
            _pathlib.open = cls.unpatched["pathlib_open"]
            _pathlib.stat = cls.unpatched["stat"]
            _pathlib.listdir = cls.unpatched["listdir"]
            _pathlib.scandir = cls.unpatched["scandir"]

        if "notebook_open" in cls.unpatched:
            import IPython.core.interactiveshell

            instance = IPython.core.interactiveshell.InteractiveShell._instance  # noqa
            if instance is not None and hasattr(instance, "user_ns"):
                instance.user_ns["open"] = cls.unpatched["notebook_open"]

        cls._uninstall_framework_hooks()
        cls.active_filesystems.clear()
        cls.is_monkey_patching = False

    _framework_key_prefix = "framework_"

    @classmethod
    def _install_framework_hooks(cls, frameworks: Optional[List[str]]):
        """
        Installs custom hook functions for frameworks
        """
        if frameworks is None:
            return
        for framework in frameworks:
            if framework not in cls._framework_override_map:
                logger.warning(f"Framework {framework} not available for override, skipping")
                continue
            funcs = cls._framework_override_map[framework]
            for func in funcs:
                module_name, func_name = func.rsplit(".", 1)
                class_name = None
                patch_class = None

                # Handle static class methods - we'll need to get the class from the module first
                if "$" in module_name:
                    module_name, class_name = module_name.split("$")
                    # Get rid of the . in the module name
                    module_name = module_name[:-1]

                try:
                    patch_module = importlib.import_module(module_name)
                    if class_name is not None:
                        patch_class = getattr(patch_module, class_name)
                        orig_fn = getattr(patch_class, func_name)
                    else:
                        orig_fn = getattr(patch_module, func_name)
                except ModuleNotFoundError:
                    logger.warning(f"Module [{module_name}] not found, so function [{func}] isn't being patched")
                    continue
                except AttributeError:
                    logger.warning(f"Function [{func}] not found, not patching it")
                    continue
                cls.unpatched[f"{cls._framework_key_prefix}{func}"] = orig_fn
                if patch_class is not None:
                    setattr(patch_class, func_name, cls._passthrough_decorator(orig_fn))
                else:
                    setattr(patch_module, func_name, cls._passthrough_decorator(orig_fn))

    @classmethod
    def _uninstall_framework_hooks(cls):
        for func in list(filter(lambda key: key.startswith(cls._framework_key_prefix), cls.unpatched.keys())):
            orig_fn = cls.unpatched[func]
            orig_func_name = func

            func = func[len(cls._framework_key_prefix) :]
            module_name, func_name = func.rsplit(".", 1)
            class_name = None

            if "$" in module_name:
                module_name, class_name = module_name.split("$")
                # Get rid of the . in the module name
                module_name = module_name[:-1]

            m = importlib.import_module(module_name)
            if class_name is not None:
                patch_class = getattr(m, class_name)
                setattr(patch_class, func_name, orig_fn)
            else:
                setattr(m, func_name, orig_fn)

            del cls.unpatched[orig_func_name]

    @classmethod
    def _passthrough_decorator(cls, orig_func, filearg: Union[int, str] = 0) -> Callable:
        """
        Decorator function over some other random function that assumes a file exists locally,
        but isn't using python's open(). These might be C++/Rust functions that use their respective opens.
        Examples: opencv, anything using pyo3

        Working around the problem by first calling open().close() to get the file.

        :param orig_func: the original function that needs to be called
        :param filearg: int or string, which arg/kwarg to use to get the filename
        :return: Wrapped orig_func
        """

        def passed_through(*args, **kwargs):
            if isinstance(filearg, str):
                filename = kwargs[filearg]
            else:
                filename = args[filearg]
            cls.open(filename).close()
            return orig_func(*args, **kwargs)

        return passed_through

    @staticmethod
    def _dagshub_path_relative_length(dhp: DagshubPath) -> int:
        if dhp.relative_path is None:
            raise RuntimeError(f"Tried to get length of the nonexistent relative path for dagshub path {dhp}")
        return len(dhp.relative_path.parents)

    @classmethod
    def determine_fs(cls, path: Union[str, bytes, PathLike]) -> Optional[DagshubPath]:
        """
        Determine the hooked filesystem that path belongs to
        If it belongs to multiple filesystems, then the one with the most specific path will be returned

        If file doesn't belong to any filesystem, then returns None
        """
        possible_paths = []
        for fs in cls.active_filesystems:
            parsed = DagshubPath(fs, path)
            if parsed.is_in_repo:
                possible_paths.append(parsed)
        if len(possible_paths) > 0:
            # Return the path that has the shortest relative path (most specific)
            return min(possible_paths, key=cls._dagshub_path_relative_length)
        return None

    @classmethod
    def get_fs_by_path(cls, path: Union[str, PathLike]) -> Optional["DagsHubFilesystem"]:
        fs: Optional["DagsHubFilesystem"] = None
        path = Path(os.path.abspath(path))
        for active_fs in cls.active_filesystems:
            if active_fs.project_root == path:
                fs = active_fs
                break
        return fs

    @classmethod
    def hook_repo(cls, fs: "DagsHubFilesystem", frameworks: Optional[List[str]]):
        if not cls.is_monkey_patching:
            cls.init_monkey_patch(frameworks)

        existing_fs = cls.get_fs_by_path(fs.project_root)
        if existing_fs is not None:
            raise FilesystemAlreadyMountedError(
                existing_fs.project_root, existing_fs.repo_api.full_name, existing_fs.current_revision
            )

        cls.active_filesystems.add(fs)

    @classmethod
    def unhook_repo(cls, fs: Optional["DagsHubFilesystem"] = None, path: Optional[Union[str, PathLike]] = None):
        if fs is None and path is None:
            raise AttributeError("Only one of `fs` or `path` should be specified at the same time")

        # Find a filesystem by path
        if path is not None:
            fs = cls.get_fs_by_path(path)
            if fs is None:
                raise RuntimeError(f"No filesystem mounted at {path}")

        # Unhook the fs
        if fs is not None and fs in cls.active_filesystems:
            cls.active_filesystems.remove(fs)

        # If there are no more filesystems anymore, unhook
        if len(cls.active_filesystems) == 0:
            cls.uninstall_monkey_patch()
