import datetime
import logging
import os
import traceback
from typing import Optional, Dict, List

import yaml

from dagshub.auth import oauth
from dagshub.common import config

logger = logging.getLogger(__name__)

APP_TOKEN_TYPE = "app-token"


class TokenStorage:
    def __init__(self, cache_location: str = None, **kwargs):
        cache_location = cache_location or config.cache_location
        self.cache_location = cache_location
        self.__token_cache: Optional[Dict[str, List[Dict]]] = None

    @property
    def _token_cache(self):
        if self.__token_cache is None:
            self.__token_cache = self._load_cache_file()
        return self.__token_cache

    def add_token(self, token: Dict, host: str = None):
        host = host or config.host
        if host not in self._token_cache:
            self._token_cache[host] = []
        self._token_cache[host].append(token)
        self._store_cache_file()

    def get_token(self, host: str = None, **kwargs):
        host = host or config.host
        tokens = self._token_cache.get(host, [])
        app_tokens = [t for t in tokens if t.get("token_type") == APP_TOKEN_TYPE]
        if len(app_tokens) > 0:
            token = app_tokens[0]
        else:
            non_expired_tokens = [t for t in tokens if not self._is_expired(t)]
            if len(non_expired_tokens) > 0:
                token = non_expired_tokens[0]
            else:
                logger.info(
                    f"No valid tokens found for host '{host}'. Authenticating with OAuth"
                )
                token = oauth.oauth_flow(host, **kwargs)
                tokens.append(token)
                self._token_cache[host] = tokens
                self._store_cache_file()
        return token["access_token"]

    @staticmethod
    def _is_expired(token: Dict[str, str]) -> bool:
        if "expiry" not in token:
            return True
        if token["expiry"] == "never":
            return False
        # Need to cut off the three additional precision numbers in milliseconds, because %f only parses 6 digits
        expiry = token["expiry"][:-4] + "Z"
        expiry_dt = datetime.datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ")
        is_expired = expiry_dt < datetime.datetime.utcnow()
        return is_expired

    def _load_cache_file(self) -> Dict[str, List[Dict]]:
        logger.debug(f"Loading OAuth token cache from {self.cache_location}")
        if not os.path.exists(self.cache_location):
            logger.debug("OAuth token cache file doesn't exist")
            return self._get_empty_cache_dict()
        try:
            with open(self.cache_location) as f:
                tokens_cache = yaml.load(f, yaml.Loader)
                return tokens_cache
        except Exception:
            logger.error(
                f"Error while loading DagsHub OAuth token cache: {traceback.format_exc()}"
            )
            raise

    @staticmethod
    def _get_empty_cache_dict():
        return {"version": config.TOKENS_CACHE_SCHEMA_VERSION}

    def _store_cache_file(self):
        logger.debug(f"Dumping OAuth token cache to {self.cache_location}")
        try:
            dirpath = os.path.dirname(self.cache_location)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            with open(self.cache_location, "w") as f:
                yaml.dump(self.__token_cache, f, yaml.Dumper)
        except Exception:
            logger.error(
                f"Error while storing DagsHub OAuth token cache: {traceback.format_exc()}"
            )
            raise


_token_storage: Optional[TokenStorage] = None


def _get_token_storage(**kwargs):
    global _token_storage
    if _token_storage is None:
        _token_storage = TokenStorage(**kwargs)
    return _token_storage


def get_token(**kwargs):
    return _get_token_storage(**kwargs).get_token(**kwargs)


def add_app_token(token: str, host: Optional[str] = None, **kwargs):
    token_dict = {
        "access_token": token,
        "token_type": APP_TOKEN_TYPE,
        "expiry": "never",
    }
    _get_token_storage(**kwargs).add_token(token_dict, host)


def add_oauth_token(host: Optional[str] = None, **kwargs):
    host = host or config.host
    token = oauth.oauth_flow(host, code_input_timeout=0)
    _get_token_storage(**kwargs).add_token(token, host)
