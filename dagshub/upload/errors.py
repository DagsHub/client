import logging
from dataclasses import dataclass
from json import JSONDecodeError

import httpx

logger = logging.getLogger(__name__)


@dataclass
class UploadErrorResponseContent:
    error: str
    details: str


@dataclass
class GenericAPIErrorContent:
    message: str


_error_lookup = {}


def register_upload_api_error(error_value: str):
    def decorator(cls):
        _error_lookup[error_value] = cls

        def __init__(self, details: str):
            self.details = details

        cls.__init__ = __init__
        return cls

    return decorator


@register_upload_api_error(error_value="missing last_commit")
class UpdateNotAllowedError(Exception):
    pass


@register_upload_api_error(error_value="invalid last_commit")
class InvalidLastCommitError(Exception):
    pass


@register_upload_api_error(error_value="versioning conflict")
class VersioningConflictError(Exception):
    pass


@register_upload_api_error(error_value="edit pipeline unsupported")
class UnsupportedStageContainerFileError(Exception):
    pass


@register_upload_api_error(error_value="path conflict")
class PathConflictError(Exception):
    pass


@register_upload_api_error(error_value="server error")
class InternalServerErrorError(Exception):
    pass


class DagsHubAPIError(Exception):
    """
    Generic API Exception, only has a message
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


def determine_upload_api_error(response: httpx.Response) -> Exception:
    try:
        json_content = response.json()
    except JSONDecodeError:
        return RuntimeError(f"Returned body wasn't valid JSON. Content: {response.content}")

    if "error" in json_content and "details" in json_content:
        error_content = UploadErrorResponseContent(json_content["error"], json_content["details"])
        error_class = _error_lookup.get(error_content.error)
        if error_class is None:
            return DagsHubAPIError(f"{error_content.error}:\n{error_content.details}")
        return error_class(error_content.details)

    elif "message" in json_content:
        return DagsHubAPIError(json_content["message"])

    return RuntimeError(response.content)
