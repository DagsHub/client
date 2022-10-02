import appdirs
import os

HOST_KEY = "DAGSHUB_CLIENT_HOST"
DEFAULT_HOST = "https://dagshub.com"
CLIENT_ID_KEY = "DAGSHUB_CLIENT_ID"
DEFAULT_CLIENT_ID = "32b60ba385aa7cecf24046d8195a71c07dd345d9657977863b52e7748e0f0f28"
CACHE_LOCATION_KEY = "DAGSHUB_CLIENT_CONFIG"
DEFAULT_CACHE_LOCATION = os.path.join(appdirs.user_cache_dir("dagshub"), "tokens")
CONFIG_SCHEMA_VERSION = "1"

host = os.environ.get(HOST_KEY, DEFAULT_HOST)
client_id = os.environ.get(CLIENT_ID_KEY, DEFAULT_CLIENT_ID)
cache_location = os.environ.get(CACHE_LOCATION_KEY, DEFAULT_CACHE_LOCATION)
