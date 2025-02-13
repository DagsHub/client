import base64
import datetime
import functools
import gzip
import types
import logging
import importlib
from pathlib import PurePath
from typing import Union, TypeVar, Dict, Optional
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


def multi_urljoin(*parts):
    """Shoutout to https://stackoverflow.com/a/55722792"""
    return urljoin(parts[0] + "/", "/".join(quote(part.strip("/"), safe="/") for part in parts[1:]))


def exclude_if_none(value):
    """For skipping serializing None values in dataclasses_json"""
    return value is None


def exclude_if_all_fields_are_none(dataclass_dict: Optional[Dict]):
    if dataclass_dict is None:
        return True
    return all(value is None for value in dataclass_dict.values())


def to_timestamp(ts: Union[float, int, datetime.datetime]) -> int:
    """
    Converts datetime objects or any timestamp-likes into an integer timestamp used by DagsHub
    """
    if isinstance(ts, datetime.datetime):
        return int(ts.timestamp())
    else:
        return int(ts)


def removeprefix(val: str, prefix: str) -> str:
    if val.startswith(prefix):
        return val[len(prefix) :]
    return val


def lazy_load(module_name, source_package=None, callback=None):
    if source_package is None:
        # TODO: need to have a map for commonly used imports here. Also handle dots
        source_package = module_name
    return LazyModule(module_name, source_package, callback)


pathSubclass = TypeVar("pathSubclass", bound=PurePath)


def is_path_relative_to(path_a: pathSubclass, path_b: pathSubclass) -> bool:
    # Polyfill of Path.is_relative
    try:
        path_a.relative_to(path_b)
        return True
    except ValueError:
        return False


class LazyModule(types.ModuleType):
    """Proxy module that lazily imports the underlying module the first time it
    is actually used.

    Shoutout to voxel51 for this :)

    Args:
        module_name: the fully-qualified module name to import
        callback (None): a callback function to call before importing the
            module
    """

    def __init__(self, module_name, source_package, callback=None):
        super().__init__(module_name)
        self._module = None
        self._callback = callback
        self._source_package = source_package

    def __getattr__(self, item):
        if self._module is None:
            self._import_module()

        return getattr(self._module, item)

    def __dir__(self):
        if self._module is None:
            self._import_module()

        return dir(self._module)

    def _import_module(self):
        # Execute callback, if any
        if self._callback is not None:
            self._callback()

        # Actually import the module
        try:
            module = importlib.import_module(self.__name__)
            self._module = module
        except ModuleNotFoundError:
            logger.warning(f"Could not import module {self.__name__}. Make sure to pip install {self._source_package}")
            raise

        # Update this object's dict so that attribute references are efficient
        # (__getattr__ is only called on lookups that fail)
        self.__dict__.update(module.__dict__)


def deprecated(additional_message=""):
    """
    Decorator to mark functions as deprecated. It will print a warning
    message when the function is called.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            additional = "\n" + additional_message if additional_message else ""
            logger.warning(
                f"DagsHub Deprecation Warning: "
                f"{func.__name__} is deprecated and may be removed in future versions.{additional}",
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def wrap_bytes(val: bytes) -> str:
    """
    Handles bytes values for uploading metadata
    The process is gzip -> base64

    :meta private:
    """
    compressed = gzip.compress(val)
    return base64.b64encode(compressed).decode("utf-8")
