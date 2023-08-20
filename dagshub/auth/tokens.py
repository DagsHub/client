import datetime
import logging
import os
import threading
import traceback
from collections import defaultdict
from typing import Optional, Dict, List, Set, Union

import yaml

from dagshub.auth import oauth
from dagshub.auth.token_auth import HTTPBearerAuth, DagshubTokenABC, TokenDeserializationError, AppDagshubToken
from dagshub.common import config
from dagshub.common.helpers import http_request
from dagshub.common.util import multi_urljoin

logger = logging.getLogger(__name__)

APP_TOKEN_TYPE = "app-token"


class InvalidTokenError(Exception):
    def __str__(self):
        print("The token is not a valid DagsHub token")


class TokenStorage:
    def __init__(self, cache_location: str = None, **kwargs):
        cache_location = cache_location or config.cache_location
        self.cache_location = cache_location
        self.schema_version = config.TOKENS_CACHE_SCHEMA_VERSION
        self.__token_cache: Optional[Dict[str, List[DagshubTokenABC]]] = None

        # We check tokens only once for validity, so we don't do a lot of redundant requests
        #   maybe there is a point to re-evaluate them once in a while
        self._known_good_tokens: Dict[str, Set[str]] = defaultdict(lambda: set())

        self._token_access_lock = threading.RLock()

    @property
    def _token_cache(self):
        if self.__token_cache is None:
            self.__token_cache = self._load_cache_file()
            self.remove_expired_tokens()
        return self.__token_cache

    def remove_expired_tokens(self):
        had_changes = False
        for host, tokens in self._token_cache.items():
            if host == "version":
                continue
            expired_tokens = filter(lambda token: token.is_expired, tokens)
            for t in expired_tokens:
                had_changes = True
                tokens.remove(t)
        if had_changes:
            logger.info("Removed expired tokens from the token cache")
            self._store_cache_file()

    def add_token(self, token: DagshubTokenABC, host: str = None, skip_validation=False):
        host = host or config.host

        if not skip_validation:
            if not TokenStorage.is_valid_token(token.token_text, host):
                raise InvalidTokenError

        if host not in self._token_cache:
            self._token_cache[host] = []
        self._token_cache[host].append(token)
        self._store_cache_file()

    def get_authenticator(self, host: str = None, fail_if_no_token: bool = False, **kwargs):
        """
        Returns the authenticator object, that can renegotiate tokens in case of failure
        """
        raise NotImplementedError

    def get_token_object(self, host: str = None, fail_if_no_token: bool = False, **kwargs) -> DagshubTokenABC:
        """
         This function does following:
         - Iterates over all tokens in the cache for the provided host
         - Finds a first valid token and returns it
         - If it finds an invalid token, it deletes it from the cache

         We're using a set of known good tokens to skip rechecking for token validity every time
         """

        # TODO: add a lock here so the access to the token storage is single threaded
        # TODO: warn on timed tokens
        # TODO: different token types

        def token_priority_sort_fn(token_dict):
            # app tokens - biggest priority
            if token_dict["token_type"] == APP_TOKEN_TYPE:
                return -1
            return 0

        with self._token_access_lock:
            host = host or config.host
            tokens = self._token_cache.get(host, [])

            had_changes = False  # For saving if we invalidate some tokens
            good_token_set = self._known_good_tokens[host]
            good_token = None
            token_queue = list(sorted(tokens, key=token_priority_sort_fn))

            for token_dict in token_queue:
                token = token_dict["access_token"]
                if token in good_token_set:
                    good_token = token_dict
                # Check token validity
                elif self.is_valid_token(token, host):
                    good_token = token_dict
                    good_token_set.add(token)
                # Remove invalid token from the cache
                else:
                    logger.debug(f"Removing invalid token {token_dict}")
                    tokens.remove(token_dict)
                    had_changes = True
                if good_token is not None:
                    break

            # Save the cache
            if had_changes:
                self._token_cache[host] = tokens
                self._store_cache_file()

            if good_token is None:
                if fail_if_no_token:
                    raise RuntimeError(
                        f"No valid tokens found for host '{host}'.\n"
                        "Log into DagsHub by executing `dagshub login` in your terminal")
                else:
                    logger.debug(
                        f"No valid tokens found for host '{host}'. Authenticating with OAuth"
                    )
                    good_token = oauth.oauth_flow(host, **kwargs)
                    tokens.append(good_token)
                    good_token_set.add(good_token["access_token"])
                    # Save the cache
                    self._token_cache[host] = tokens
                    self._store_cache_file()

            return good_token["access_token"]

    def get_token(self, host: str = None, fail_if_no_token: bool = False, **kwargs) -> str:
        """
        Return the raw token string
        This is a lower level method that cannot do renegotiations, we only return the token itself here.
        Used mainly for setting environment variables, for example for MLflow
        """
        return self.get_token_object(host, fail_if_no_token).token_text

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

    @staticmethod
    def is_valid_token(token: str, host: str) -> bool:
        """
        Check for token validity

        Args:
            token: token to check validity
            host: which host to connect against
        """
        host = host or config.host
        check_url = multi_urljoin(host, "api/v1/user")
        auth = HTTPBearerAuth(token)
        resp = http_request("GET", check_url, auth=auth)

        try:
            # 500's might be ok since they're server errors, so check only for 400's
            assert not (400 <= resp.status_code <= 499)
            if resp.status_code == 200:
                assert "login" in resp.json()
            return True
        except AssertionError:
            return False

    def _load_cache_file(self) -> Dict[str, List[DagshubTokenABC]]:
        logger.debug(f"Loading OAuth token cache from {self.cache_location}")
        if not os.path.exists(self.cache_location):
            logger.debug("OAuth token cache file doesn't exist")
            return {}
        try:
            with open(self.cache_location) as f:
                cache_yaml = yaml.load(f, yaml.Loader)
                version = cache_yaml.get("version", "1")
                if version == "1":
                    return self._v1_token_list_parser(cache_yaml)
                raise RuntimeError(f"Don't know how to parse token schema {version}")
        except Exception:
            logger.error(
                f"Error while loading DagsHub OAuth token cache: {traceback.format_exc()}"
            )
            raise

    @staticmethod
    def _v1_token_list_parser(cache_yaml: Dict[str, Union[str, List[Dict]]]) -> Dict[str, List[DagshubTokenABC]]:
        res = {}

        token_class_map = {}
        for token_class in DagshubTokenABC.__subclasses__():
            token_class_map[token_class.token_type] = token_class

        for host, tokens in cache_yaml.items():
            if host == "version":
                continue
            if len(tokens) == 0:
                continue
            host_tokens = []
            for token_dict in tokens:
                try:
                    token = token_class_map[token_dict["token_type"]].deserialize(token_dict)
                    host_tokens.append(token)
                except TokenDeserializationError as e:
                    logger.warning(f"Failed to deserialize token {token_dict}: {e}")
            res[host] = host_tokens
        return res

    def _store_cache_file(self):
        logger.debug(f"Dumping OAuth token cache to {self.cache_location}")
        try:
            dirpath = os.path.dirname(self.cache_location)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            dict_to_dump = {"version": self.schema_version}
            for host, tokens in self.__token_cache.items():
                dict_to_dump[host] = [t.serialize() for t in tokens]
            with open(self.cache_location, "w") as f:
                yaml.dump(dict_to_dump, f, yaml.Dumper)
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
    """
    Gets a DagsHub token, by default if no token is found authenticates with OAuth

    Kwargs:
        host (str): URL of a dagshub instance (defaults to dagshub.com)
        cache_location (str): Location of the cache file with the token (defaults to <cache_dir>/dagshub/tokens)
        fail_if_no_token (bool): What to do if token is not found.
            If set to False (default), goes through OAuth flow
            If set to True, throws a RuntimeError
    """
    return _get_token_storage(**kwargs).get_token(**kwargs)


def add_app_token(token: str, host: Optional[str] = None, **kwargs):
    """
    Adds an application token to the token cache.
    This is a long-lived token that you can add/revoke in your profile settings on DagsHub
    """
    token_obj = AppDagshubToken(token)
    _get_token_storage(**kwargs).add_token(token_obj, host)


def add_oauth_token(host: Optional[str] = None, **kwargs):
    """
    Launches the OAuth flow that generates a short-lived token.
    This will open a new browser window, so this is not a CI/headless friendly function.
    Consider using `add_app_token` or setting the `DAGSHUB_USER_TOKEN` env var in those cases.
    """
    host = host or config.host
    token = oauth.oauth_flow(host)
    _get_token_storage(**kwargs).add_token(token, host, skip_validation=True)
