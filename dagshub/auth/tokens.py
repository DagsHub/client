import datetime
import logging
import os
import threading
import traceback
from typing import Optional, Dict, List, Set, Union, cast

import yaml
from httpx import Auth

from dagshub.auth import oauth
from dagshub.auth.token_auth import (
    HTTPBearerAuth,
    DagshubTokenABC,
    TokenDeserializationError,
    AppDagshubToken,
    EnvVarDagshubToken,
    DagshubAuthenticator,
)
from dagshub.common import config
from dagshub.common.helpers import http_request, log_message
from dagshub.common.util import multi_urljoin

logger = logging.getLogger(__name__)

APP_TOKEN_TYPE = "app-token"


class InvalidTokenError(Exception):
    def __str__(self):
        print("The token is not a valid DagsHub token")


_validated_env_tokens = set()


class TokenStorage:
    def __init__(self, cache_location: Optional[str] = None, **kwargs):
        cache_location = cache_location or config.cache_location
        self.cache_location = cache_location
        self.schema_version = config.TOKENS_CACHE_SCHEMA_VERSION
        self.__token_cache: Optional[Dict[str, List[DagshubTokenABC]]] = None

        # We check tokens only once for validity, so we don't do a lot of redundant requests
        #   maybe there is a point to re-evaluate them once in a while
        self._known_good_tokens: Dict[str, Set[DagshubTokenABC]] = {}

        self.__token_access_lock = threading.RLock()
        self._accessing_as_was_printed = False

    @property
    def _token_cache(self):
        if self.__token_cache is None:
            self.__token_cache = self._load_cache_file()
            self.remove_expired_tokens()
        return self.__token_cache

    @property
    def _token_access_lock(self):
        if not hasattr(self, "__token_access_lock"):
            self.__token_access_lock = threading.RLock()
        return self.__token_access_lock

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

    def add_token(self, token: Union[str, DagshubTokenABC], host: Optional[str] = None, skip_validation=False):
        host = host or config.host

        if isinstance(token, str):
            token = AppDagshubToken(token)

        token = cast(DagshubTokenABC, token)

        if self._token_already_exists(token.token_text, host):
            logger.warning("The added token already exists in the token cache, skipping")
            return

        if not skip_validation:
            if not TokenStorage.is_valid_token(token.token_text, host):
                raise InvalidTokenError

        if host not in self._token_cache:
            self._token_cache[host] = []
        self._token_cache[host].append(token)
        self._store_cache_file()

    def invalidate_token(self, token: DagshubTokenABC, host: Optional[str] = None):
        host = host or config.host

        try:
            if host in self._token_cache:
                tokens = self._token_cache[host]
                tokens.remove(token)

                if host in self._known_good_tokens:
                    good_token_set = self._known_good_tokens[host]
                    if token in good_token_set:
                        good_token_set.remove(token)

                self._store_cache_file()
        except ValueError:
            logger.warning(f"Token {token} does not exist in the storage")

    def get_authenticator(
        self, host: Optional[str] = None, fail_if_no_token: bool = False, **kwargs
    ) -> DagshubAuthenticator:
        """
        Returns the authenticator object, that can renegotiate tokens in case of failure
        """
        host = host or config.host
        token = self.get_token_object(host, fail_if_no_token, **kwargs)
        return DagshubAuthenticator(token, token_storage=self, host=host)

    def get_token_object(self, host: Optional[str] = None, fail_if_no_token: bool = False, **kwargs) -> DagshubTokenABC:
        """
        This function does following:
        - Iterates over all tokens in the cache for the provided host
        - Finds a first valid token and returns it
        - If it finds an invalid token, it deletes it from the cache

        We're using a set of known good tokens to skip rechecking for token validity every time
        """

        host = host or config.host
        if host == config.host and config.token is not None:
            if config.token not in _validated_env_tokens:
                user = TokenStorage.get_username_of_token(config.token, host)
                if user is not None:
                    self._print_accessing_as(user)
                    _validated_env_tokens.add(config.token)
                else:
                    raise RuntimeError("Provided DagsHub token is not valid")
            return EnvVarDagshubToken(config.token, host)

        with self._token_access_lock:
            tokens = self._token_cache.get(host, [])

            if host not in self._known_good_tokens:
                self._known_good_tokens[host] = set()
            good_token_set = self._known_good_tokens[host]
            good_token = None
            good_user = None
            token_queue = list(sorted(tokens, key=lambda t: t.priority))

            for token in token_queue:
                if token.is_expired:
                    self.invalidate_token(token, host)
                    good_token_set = self._known_good_tokens[host]

                if token in good_token_set:
                    good_token = token
                    break
                # Check token validity
                user = TokenStorage.get_username_of_token(token, host)
                if user is not None:
                    good_token = token
                    good_token_set.add(token)
                    good_user = user
                # Remove invalid token from the cache
                else:
                    self.invalidate_token(token, host)
                    good_token_set = self._known_good_tokens[host]
                if good_token is not None:
                    break

            # Couldn't manage to find a good token after the search
            # Either go through the oauth flow, or throw a runtime error
            if good_token is None:
                if fail_if_no_token:
                    raise RuntimeError(
                        f"No valid tokens found for host '{host}'.\n"
                        "Log into DagsHub by executing `dagshub login` in your terminal"
                    )
                else:
                    logger.debug(f"No valid tokens found for host '{host}'. Authenticating with OAuth")
                    good_token = oauth.oauth_flow(host, **kwargs)
                    tokens.append(good_token)
                    good_token_set.add(good_token)
                    good_user = TokenStorage.get_username_of_token(good_token, host)
                    # Save the cache
                    self._token_cache[host] = tokens
                    self._store_cache_file()

            self._print_accessing_as(good_user)
            return good_token

    def get_token(self, host: Optional[str] = None, fail_if_no_token: bool = False, **kwargs) -> str:
        """
        Return the raw token string
        This is a lower level method that cannot do renegotiations, we only return the token itself here.
        Used mainly for setting environment variables, for example for MLflow
        """
        return self.get_token_object(host, fail_if_no_token).token_text

    def _token_already_exists(self, token_text: str, host: str):
        for token in self._token_cache.get(host, []):
            if token.token_text == token_text:
                return True
        return False

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
    def get_username_of_token(token: Union[str, Auth, DagshubTokenABC], host: str) -> Optional[Dict]:
        """
        Check for token validity and return the dictionary with the info of the user of the token

        Args:
            token: token to check validity
            host: which host to connect against
        """
        host = host or config.host
        check_url = multi_urljoin(host, "api/v1/user")
        if type(token) is str:
            auth = HTTPBearerAuth(token)
        else:
            auth = token
        resp = http_request("GET", check_url, auth=auth)

        try:
            assert resp.status_code == 200
            user = resp.json()
            assert "login" in user
            assert "username" in user
            return user
        except AssertionError:
            return None

    @staticmethod
    def is_valid_token(token: Union[str, Auth, DagshubTokenABC], host: str) -> bool:
        """
        Check for token validity

        Args:
            token: token to check validity
            host: which host to connect against
        """
        return TokenStorage.get_username_of_token(token, host) is not None

    def _load_cache_file(self) -> Dict[str, List[DagshubTokenABC]]:
        logger.debug(f"Loading token cache from {self.cache_location}")
        if not os.path.exists(self.cache_location):
            logger.debug("Token cache file doesn't exist")
            return {}
        try:
            with open(self.cache_location) as f:
                cache_yaml = yaml.load(f, yaml.Loader)
                version = cache_yaml.get("version", "1")
                if version == "1":
                    return self._v1_token_list_parser(cache_yaml)
                raise RuntimeError(f"Don't know how to parse token schema {version}")
        except Exception:
            logger.error(f"Error while loading DagsHub token cache: {traceback.format_exc()}")
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
        logger.debug(f"Dumping token cache to {self.cache_location}")
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
            logger.error(f"Error while storing DagsHub token cache: {traceback.format_exc()}")
            raise

    def _print_accessing_as(self, user: Dict):
        """
        This function prints a message to the log that we are accessing as a certain user.
        It does this only once per command, to avoid spamming the logs.
        It called after successful token validation.

        """
        if self._accessing_as_was_printed:
            return

        username = user["username"]

        log_message(f"Accessing as {username}")
        self._accessing_as_was_printed = True

    def __getstate__(self):
        d = self.__dict__
        # Don't pickle the lock. This will make it so multiple authenticators might request for tokens at the same time
        # This can lead to e.g. multiple OAuth requests firing at the same time, which is not desirable
        # However, I'm not sure of a good way to solve it
        access_lock_key = f"_{self.__class__.__name__}__token_access_lock"
        if access_lock_key in d:
            del d[access_lock_key]
        return d

    def __setstate__(self, state):
        self.__dict__ = state


_token_storage: Optional[TokenStorage] = None


def _get_token_storage(**kwargs):
    global _token_storage
    if _token_storage is None:
        _token_storage = TokenStorage(**kwargs)
    return _token_storage


def get_authenticator(**kwargs) -> DagshubAuthenticator:
    """
    Get an authenticator object that can be used to authenticate a request to DagsHub using an http library like
    ``httpx`` or ``requests``.

    When used with ``httpx``, the authenticator has renegotiation logic. That means that if DagsHub rejects a token,
    the authenticator will try to get another token from the cache, or fall back to OAuth.

    If no valid token was found and ``fail_if_no_token`` wasn't set to ``True``, triggers OAuth flow.

    Keyword Args:
        fail_if_no_token: Whether to get an OAuth token if no valid token was found in cache initially.
            If set to ``True``, raises a ``RuntimeError``.
            If set to ``False`` (default), launches the OAuth flow.
        cache_location: Path to an alternative cache location.
            You can override the default cache location to be used by the client by setting the
            ``DAGSHUB_CLIENT_TOKENS_CACHE`` environment variable.
        host: URL of the hosted DagsHub instance. default is ``https://dagshub.com``.

    """
    return _get_token_storage(**kwargs).get_authenticator(**kwargs)


def get_token_object(**kwargs):
    """
    Gets a DagsHub token object, by default if no token is found authenticates with OAuth.
    The token object has additional information about the type and expiry of the token.

    Keyword Args:
        fail_if_no_token: Whether to get an OAuth token if no valid token was found in cache initially.
            If set to ``True``, raises a ``RuntimeError``.
            If set to ``False`` (default), launches the OAuth flow.
        cache_location: Path to an alternative cache location.
            You can override the default cache location to be used by the client by setting the
            ``DAGSHUB_CLIENT_TOKENS_CACHE`` environment variable.
        host: URL of the hosted DagsHub instance. default is ``https://dagshub.com``.

    """
    return _get_token_storage(**kwargs).get_token_object(**kwargs)


def get_token(**kwargs) -> str:
    """
    Gets a DagsHub token in regular string form.

    Use this function when you want to, for example,
    manually authenticate with DagsHub's MLflow using ``MLFLOW_TRACKING_PASSWORD``.

    If no valid token was found and ``fail_if_no_token`` wasn't set to ``True``, triggers OAuth flow.


    Keyword Args:
        fail_if_no_token: Whether to get an OAuth token if no valid token was found in cache initially.
            If set to ``True``, raises a ``RuntimeError``.
            If set to ``False`` (default), launches the OAuth flow.
        cache_location: Path to an alternative cache location.
            You can override the default cache location to be used by the client by setting the
            ``DAGSHUB_CLIENT_TOKENS_CACHE`` environment variable.
        host: URL of the hosted DagsHub instance. default is ``https://dagshub.com``.

    """
    return _get_token_storage(**kwargs).get_token(**kwargs)


def add_app_token(token: str, host: Optional[str] = None, **kwargs):
    """
    Adds an application token to the token cache.
    This is a long-lived token that you can add/revoke in your profile settings on DagsHub.

    Args:
        token: Token value
        host: URL of the hosted DagsHub instance. Leave empty to use the default ``https://dagshub.com``.

    Keyword Args:
        cache_location: Path to an alternative cache location.
            You can override the default cache location to be used by the client by setting the
            ``DAGSHUB_CLIENT_TOKENS_CACHE`` environment variable.
    """
    token_obj = AppDagshubToken(token)
    _get_token_storage(**kwargs).add_token(token_obj, host)


def add_oauth_token(host: Optional[str] = None, referrer: Optional[str] = None, **kwargs):
    """
    Launches the OAuth flow that generates a short-lived token.

    .. note::
        This will open a new browser window, so this is not a CI/headless friendly function.
        Consider using :func:`.add_app_token` or setting the ``DAGSHUB_USER_TOKEN`` env var in those cases.

    Args:
        host: URL of the hosted DagsHub instance. Leave empty to use the default ``https://dagshub.com``.
        referrer: For custom referral flows

    Keyword Args:
        cache_location: Path to an alternative cache location.
            You can override the default cache location to be used by the client by setting the
            ``DAGSHUB_CLIENT_TOKENS_CACHE`` environment variable.
    """
    host = host or config.host
    token = oauth.oauth_flow(host, referrer=referrer)
    _get_token_storage(**kwargs).add_token(token, host, skip_validation=True)
