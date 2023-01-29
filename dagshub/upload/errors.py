import functools
from dataclasses import dataclass

import httpx


@dataclass
class UploadErrorResponseContent:
    error: str
    details: str


@dataclass
class GenericAPIErrorContent:
    message: str


_error_lookup = {}


def _error_name(error: str):
    def decorator(cls):
        _error_lookup[error] = cls

        def __init__(self, details: str):
            self.details = details
        cls.__init__ = __init__
        return cls
    return decorator


@_error_name("missing last_commit")
class UpdateNotAllowedError(Exception):
    pass


@_error_name("invalid last_commit")
class InvalidLastCommitError(Exception):
    pass


@_error_name("versioning conflict")
class VersioningConflictError(Exception):
    pass


@_error_name("edit pipeline unsupported")
class UnsupportedStageContainerFileError(Exception):
    pass


@_error_name("path conflict")
class PathConflictError(Exception):
    pass


@_error_name("server error")
class InternalServerErrorError(Exception):
    pass


class DagsHubAPIError(Exception):
    """
    Generic API Exception, only has a message
    """
    def __init__(self, message: str):
        super().__init__()
        self.message = message


def determine_error(response: httpx.Response) -> Exception:
    try:
        json_content = response.json()
    except Exception as e:
        return e

    if "error" in json_content and "details" in json_content:
        error_content = UploadErrorResponseContent(json_content["error"], json_content["details"])
        error_class = _error_lookup.get(error_content.error)
        if error_class is None:
            return DagsHubAPIError(f"{error_content.error}:\n{error_content.details}")
        return error_class(error_content.details)

    elif "message" in json_content:
        return DagsHubAPIError(json_content["message"])

    return RuntimeError(response.content)
