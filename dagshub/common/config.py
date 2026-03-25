import logging
import os
from urllib.parse import urlparse

import appdirs
from httpx._client import USER_AGENT

from dagshub import __version__

logger = logging.getLogger(__name__)

HOST_KEY = "DAGSHUB_CLIENT_HOST"
DEFAULT_HOST = "https://dagshub.com"
CLIENT_ID_KEY = "DAGSHUB_CLIENT_ID"
DEFAULT_CLIENT_ID = "32b60ba385aa7cecf24046d8195a71c07dd345d9657977863b52e7748e0f0f28"
TOKENS_CACHE_LOCATION_KEY = "DAGSHUB_CLIENT_TOKENS_CACHE"
DEFAULT_TOKENS_CACHE_LOCATION = os.path.join(appdirs.user_cache_dir("dagshub"), "tokens")
TOKENS_CACHE_SCHEMA_VERSION = "1"
DAGSHUB_USER_TOKEN_KEY = "DAGSHUB_USER_TOKEN"
DAGSHUB_USERNAME_KEY = "DAGSHUB_USERNAME"
DAGSHUB_PASSWORD_KEY = "DAGSHUB_PASSWORD"
HTTP_TIMEOUT_KEY = "DAGSHUB_HTTP_TIMEOUT"
DAGSHUB_QUIET_KEY = "DAGSHUB_QUIET"
DISABLE_TRACEPARENT_KEY = "DAGSHUB_DISABLE_TRACEPARENT"


def set_host(new_host: str):
    _parsed_host = urlparse(new_host)
    _hostname = _parsed_host.hostname
    _host = _parsed_host.geturl().rstrip("/")

    global hostname, host, parsed_host
    hostname, host, parsed_host = _hostname, _host, _parsed_host


hostname = ""
host = ""
parsed_host = ""
set_host(os.environ.get(HOST_KEY, DEFAULT_HOST))

client_id = os.environ.get(CLIENT_ID_KEY, DEFAULT_CLIENT_ID)
cache_location = os.environ.get(TOKENS_CACHE_LOCATION_KEY, DEFAULT_TOKENS_CACHE_LOCATION)
token = os.environ.get(DAGSHUB_USER_TOKEN_KEY)
username = os.environ.get(DAGSHUB_USERNAME_KEY)
password = os.environ.get(DAGSHUB_PASSWORD_KEY)
custom_user_agent_suffix = f" dagshub-client-python/{__version__}"
requests_headers = {"user-agent": USER_AGENT + custom_user_agent_suffix}
http_timeout = os.environ.get(HTTP_TIMEOUT_KEY, 30)
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"

quiet = bool(os.environ.get(DAGSHUB_QUIET_KEY, False))

disable_traceparent = bool(os.environ.get(DISABLE_TRACEPARENT_KEY, False))

# DVC config templates
CONFIG_GITIGNORE = "/config.local\n/tmp\n/cache"

RECOMMENDED_ANNOTATE_LIMIT_KEY = "RECOMMENDED_ANNOTATE_LIMIT"
recommended_annotate_limit = int(os.environ.get(RECOMMENDED_ANNOTATE_LIMIT_KEY, 1e5))

DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_KEY = "DAGSHUB_DE_METADATA_UPLOAD_BATCH_SIZE"
DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MAX_KEY = "DAGSHUB_DE_METADATA_UPLOAD_BATCH_SIZE_MAX"
DEFAULT_DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MAX = 50000
# Fall back to the old `DAGSHUB_DE_METADATA_UPLOAD_BATCH_SIZE` env var for backwards compatibility.
dataengine_metadata_upload_batch_size_max = int(
    os.environ.get(
        DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MAX_KEY,
        os.environ.get(DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_KEY, DEFAULT_DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MAX),
    )
)

DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MIN_KEY = "DAGSHUB_DE_METADATA_UPLOAD_BATCH_SIZE_MIN"
dataengine_metadata_upload_batch_size_min = int(os.environ.get(DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_MIN_KEY, 1))

DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_INITIAL_KEY = "DAGSHUB_DE_METADATA_UPLOAD_BATCH_SIZE_INITIAL"
dataengine_metadata_upload_batch_size_initial = int(
    os.environ.get(DATAENGINE_METADATA_UPLOAD_BATCH_SIZE_INITIAL_KEY, dataengine_metadata_upload_batch_size_min)
)

DATAENGINE_METADATA_UPLOAD_TARGET_BATCH_TIME_SECONDS_KEY = "DAGSHUB_DE_METADATA_UPLOAD_TARGET_BATCH_TIME_SECONDS"
dataengine_metadata_upload_target_batch_time_seconds = float(
    os.environ.get(DATAENGINE_METADATA_UPLOAD_TARGET_BATCH_TIME_SECONDS_KEY, 5.0)
)

DATAENGINE_METADATA_UPLOAD_BATCH_GROWTH_FACTOR_KEY = "DAGSHUB_DE_METADATA_UPLOAD_BATCH_GROWTH_FACTOR"
adaptive_batch_growth_factor = int(os.environ.get(DATAENGINE_METADATA_UPLOAD_BATCH_GROWTH_FACTOR_KEY, 10))

DATAENGINE_METADATA_UPLOAD_RETRY_BACKOFF_BASE_KEY = "DAGSHUB_DE_METADATA_UPLOAD_RETRY_BACKOFF_BASE"
adaptive_batch_retry_backoff_base_seconds = float(
    os.environ.get(DATAENGINE_METADATA_UPLOAD_RETRY_BACKOFF_BASE_KEY, 0.25)
)

DATAENGINE_METADATA_UPLOAD_RETRY_BACKOFF_MAX_KEY = "DAGSHUB_DE_METADATA_UPLOAD_RETRY_BACKOFF_MAX"
adaptive_batch_retry_backoff_max_seconds = float(os.environ.get(DATAENGINE_METADATA_UPLOAD_RETRY_BACKOFF_MAX_KEY, 60.0))

DISABLE_ANALYTICS_KEY = "DAGSHUB_DISABLE_ANALYTICS"
disable_analytics = "DAGSHUB_DISABLE_ANALYTICS" in os.environ

DOWNLOAD_THREADS_KEY = "DAGSHUB_DOWNLOAD_THREADS"
DEFAULT_DOWNLOAD_THREADS = 32
download_threads = int(os.environ.get(DOWNLOAD_THREADS_KEY, DEFAULT_DOWNLOAD_THREADS))

UPLOAD_THREADS_KEY = "DAGSHUB_UPLOAD_THREADS"
DEFAULT_UPLOAD_THREADS = 8
upload_threads = int(os.environ.get(UPLOAD_THREADS_KEY, DEFAULT_UPLOAD_THREADS))

if download_threads > DEFAULT_DOWNLOAD_THREADS:
    logger.warning(
        f"Number of download threads was set to {download_threads}. "
        f"We recommend lowering the value if you get met with rate limits"
    )
