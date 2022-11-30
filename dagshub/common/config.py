import appdirs
import os
from urllib.parse import urlparse
from dagshub import __version__
from httpx._client import USER_AGENT

HOST_KEY = "DAGSHUB_CLIENT_HOST"
DEFAULT_HOST = "https://dagshub.com"
CLIENT_ID_KEY = "DAGSHUB_CLIENT_ID"
DEFAULT_CLIENT_ID = "32b60ba385aa7cecf24046d8195a71c07dd345d9657977863b52e7748e0f0f28"
TOKENS_CACHE_LOCATION_KEY = "DAGSHUB_CLIENT_TOKENS_CACHE"
DEFAULT_TOKENS_CACHE_LOCATION = os.path.join(
    appdirs.user_cache_dir("dagshub"), "tokens"
)
TOKENS_CACHE_SCHEMA_VERSION = "1"
DAGSHUB_USER_TOKEN_KEY = "DAGSHUB_USER_TOKEN"
DAGSHUB_USERNAME_KEY = "DAGSHUB_USERNAME"
DAGSHUB_PASSWORD_KEY = "DAGSHUB_PASSWORD"
HTTP_TIMEOUT_KEY = "DAGSHUB_HTTP_TIMEOUT"

parsed_host = urlparse(os.environ.get(HOST_KEY, DEFAULT_HOST))
hostname = parsed_host.hostname
host = parsed_host.geturl()
client_id = os.environ.get(CLIENT_ID_KEY, DEFAULT_CLIENT_ID)
cache_location = os.environ.get(
    TOKENS_CACHE_LOCATION_KEY, DEFAULT_TOKENS_CACHE_LOCATION
)
token = os.environ.get(DAGSHUB_USER_TOKEN_KEY)
username = os.environ.get(DAGSHUB_USERNAME_KEY)
password = os.environ.get(DAGSHUB_PASSWORD_KEY)
custom_user_agent_suffix = f" dagshub-client-python/{__version__}"
requests_headers = {"user-agent": USER_AGENT + custom_user_agent_suffix}
http_timeout = os.environ.get(HTTP_TIMEOUT_KEY, 30)
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"
