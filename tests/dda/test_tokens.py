import datetime

import dateutil.parser
import httpx
import pytest

import dagshub.common.config
from dagshub.auth.token_auth import AppDagshubToken, DagshubTokenABC, OAuthDagshubToken, EnvVarDagshubToken
from dagshub.auth.tokens import (
    TokenStorage,
    InvalidTokenError,
)


@pytest.fixture
def token_api(mock_api):
    # Disable the env var token for these tests explicitly
    old_token_val = dagshub.common.config.token
    dagshub.common.config.token = None

    mock_api.post("https://dagshub.com/api/v1/middleman").mock(httpx.Response(200, json="code"))

    a_day_away = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    good_auth_token = {
        "access_token": "good-token",
        "expiry": a_day_away.isoformat(),
        "token_type": "bearer",
    }
    mock_api.post("https://dagshub.com/api/v1/access_token").mock(httpx.Response(200, json=good_auth_token))
    yield mock_api

    dagshub.common.config.token = old_token_val


@pytest.fixture
def token_cache(token_api, tmp_path) -> TokenStorage:
    cache_file = tmp_path / "tokens"
    storage = TokenStorage(cache_location=str(cache_file.absolute()))
    yield storage


@pytest.fixture
def valid_token() -> DagshubTokenABC:
    return AppDagshubToken("good-token")


@pytest.fixture
def invalid_token() -> DagshubTokenABC:
    return AppDagshubToken("fake-token")


@pytest.fixture
def expired_token() -> DagshubTokenABC:
    old_date = dateutil.parser.parse("1990-01-01T16:24:53.451259Z")
    return OAuthDagshubToken("fake-token", old_date)


def test_no_token_fails_if_set_to_fail(token_cache):
    with pytest.raises(RuntimeError):
        token_cache.get_token(fail_if_no_token=True)


def test_cant_add_invalid_token(token_cache, invalid_token):
    with pytest.raises(InvalidTokenError):
        token_cache.add_token(invalid_token)


def test_can_add_valid_token(token_cache, valid_token):
    # Assume there is a known good token in the regular get_token flow
    token_cache.add_token(valid_token)


def test_expired_token_gets_cleaned_up(token_cache, expired_token):
    token_cleanup_test(token_cache, expired_token)


def test_invalid_token_gets_cleaned_up(token_cache, invalid_token):
    token_cleanup_test(token_cache, invalid_token)


def token_cleanup_test(token_cache, token):
    token_cache.add_token(token, skip_validation=True)

    with pytest.raises(RuntimeError):
        token_cache.get_token(fail_if_no_token=True)
    # Also call this to remove expired tokens
    token_cache.remove_expired_tokens()

    # Check that the token got deleted from the file
    failed = False
    with open(token_cache.cache_location, "r") as f:
        for line in f.readlines():
            if token.token_text in line:
                failed = True
                break
    print(token_cache.cache_location)
    assert not failed


def test_token_addition(token_cache, valid_token):
    token_cache.add_token(valid_token, skip_validation=True)
    passed = False
    with open(token_cache.cache_location, "r") as f:
        for line in f.readlines():
            if valid_token.token_text in line:
                passed = True
                break
    assert passed


def test_token_validity(token_cache, valid_token):
    assert token_cache.is_valid_token(valid_token, host=dagshub.common.config.host)


def test_valid_token_gets_returned(token_cache, valid_token, invalid_token):
    token_cache.add_token(valid_token, skip_validation=True)
    token_cache.add_token(invalid_token, skip_validation=True)

    actual = token_cache.get_token()
    assert actual == valid_token.token_text


def test_env_var_tokens_gets_returned_no_matter_what(token_cache, valid_token):
    token_cache.add_token(valid_token, skip_validation=True)

    old_val = dagshub.common.config.token
    val = "token-set-in-env-var"
    try:
        dagshub.common.config.token = val
        actual = token_cache.get_token_object()

        assert type(actual) is EnvVarDagshubToken
        assert actual.token_text == val
    finally:
        dagshub.common.config.token = old_val


# The authenticator needs to be picklable in order to work in multiprocess environment
def test_authenticator_is_picklable(token_cache, valid_token):
    import pickle

    token_cache.add_token(valid_token, skip_validation=True)
    auth = token_cache.get_authenticator()
    pickled_auth = pickle.dumps(auth)
    unpickled_auth = pickle.loads(pickled_auth)
    assert auth.token_text == unpickled_auth.token_text
