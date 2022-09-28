import appdirs
import datetime
import getpass
import logging
import os
import requests
import traceback
from typing import Optional, Dict
import uuid
import yaml

HOST_KEY = "DAGSHUB_CLIENT_HOST"
DEFAULT_HOST = "https://dagshub.com"
CACHE_LOCATION_KEY = "DAGSHUB_CLIENT_CONFIG"
DEFAULT_CACHE_LOCATION = os.path.join(appdirs.user_cache_dir("dagshub"), "tokens")
CLIENT_ID_KEY = "DAGSHUB_CLIENT_ID"
DEFAULT_CLIENT_ID = "32b60ba385aa7cecf24046d8195a71c07dd345d9657977863b52e7748e0f0f28"

logger = logging.getLogger(__name__)


class OAuthAuthenticator:
    def __init__(self, **kwargs):
        self.host: str = kwargs.get("host", os.environ.get(HOST_KEY, DEFAULT_HOST))
        self.client_id: str = kwargs.get(
            "client_id", os.environ.get(CLIENT_ID_KEY, DEFAULT_CLIENT_ID)
        )
        self.cache_location: str = kwargs.get(
            "cache_location", os.environ.get(CACHE_LOCATION_KEY, DEFAULT_CACHE_LOCATION)
        )
        self._token_cache: Optional[Dict[str, Dict]] = None

    def get_oauth_token(self) -> str:
        if self._token_cache is None:
            self._token_cache = self._load_cache_file()
        token = self._token_cache.get(self.host, None)
        if token is None or self._is_expired(token):
            token = self.oauth_flow()
            self._token_cache[self.host] = token
            self._store_cache_file()
        return token["access_token"]

    def oauth_flow(self) -> Dict:
        state = uuid.uuid4()
        dagshub_url = f"{self.host}/login/oauth"
        print(
            f"Go to {dagshub_url}/authorize?state={state}&client_id={self.client_id} and paste the code back in here."
        )
        code = getpass.getpass("Code:")
        res = requests.post(
            f"{dagshub_url}/access_token",
            data={"client_id": self.client_id, "code": code, "state": state},
        )
        if res.status_code != 200:
            raise Exception(
                f"Error while getting OAuth token: HTTP {res.status_code}, Body: {res.json()}"
            )
        token = res.json()
        logger.debug(f"Got token: {token}")
        return token

    @staticmethod
    def _is_expired(token: Dict[str, str]) -> bool:
        if "expiry" not in token:
            return True
        # Need to cut off the three additional precision numbers in milliseconds, because %f only parses 6 digits
        expiry = token["expiry"][:-4] + "Z"
        expiry_dt = datetime.datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ")
        is_expired = expiry_dt < datetime.datetime.utcnow()
        if is_expired:
            logger.warning("OAuth token expired, need to reauthenticate")
        return is_expired

    def _load_cache_file(self) -> Optional[Dict[str, Dict]]:
        logger.debug(f"Loading OAuth token cache from {self.cache_location}")
        if not os.path.exists(self.cache_location):
            logger.debug("OAuth token cache file doesn't exist")
            return {}
        try:
            with open(self.cache_location) as f:
                tokens_cache = yaml.load(f, yaml.Loader)
                return tokens_cache
        except:
            logger.error(
                f"Error while loading DagsHub OAuth token cache: {traceback.format_exc()}"
            )
            raise

    def _store_cache_file(self):
        logger.debug(f"Dumping OAuth token cache to {self.cache_location}")
        try:
            dirpath = os.path.dirname(self.cache_location)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            with open(self.cache_location, "w") as f:
                yaml.dump(self._token_cache, f, yaml.Dumper)
        except:
            logger.error(
                f"Error while storing DagsHub OAuth token cache: {traceback.format_exc()}"
            )
            raise


_authenticator: Optional[OAuthAuthenticator] = None


def get_oauth_token() -> str:
    global _authenticator
    if _authenticator is None:
        _authenticator = OAuthAuthenticator()
    return _authenticator.get_oauth_token()


def console_entrypoint():
    get_oauth_token()
    print(
        f"Your DagsHub OAuth token is now stored at {_authenticator.cache_location}"
        f" and will be used next time you use the client"
    )


if __name__ == "__main__":
    # For debug
    logging.basicConfig(level=logging.DEBUG)
    logger.info(get_oauth_token())
