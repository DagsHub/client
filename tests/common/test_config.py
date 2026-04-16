import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

CONFIG_PATH = Path(__file__).resolve().parents[2] / "dagshub" / "common" / "config.py"


def load_config_module():
    fake_dagshub = types.ModuleType("dagshub")
    fake_dagshub.__version__ = "test-version"

    fake_appdirs = types.ModuleType("appdirs")
    fake_appdirs.user_cache_dir = lambda app_name: f"/tmp/{app_name}"

    fake_httpx = types.ModuleType("httpx")
    fake_httpx_client = types.ModuleType("httpx._client")
    fake_httpx_client.USER_AGENT = "test-agent"

    spec = importlib.util.spec_from_file_location("test_dagshub_common_config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "dagshub": fake_dagshub,
            "appdirs": fake_appdirs,
            "httpx": fake_httpx,
            "httpx._client": fake_httpx_client,
        },
    ):
        spec.loader.exec_module(module)
    return module


class ConfigTestCase(unittest.TestCase):
    def test_boolean_env_flags_are_parsed_from_string_values(self):
        with patch.dict(
            os.environ,
            {
                "DAGSHUB_QUIET": "false",
                "DAGSHUB_DISABLE_TRACEPARENT": "1",
            },
            clear=False,
        ):
            config = load_config_module()

        self.assertFalse(config.quiet)
        self.assertTrue(config.disable_traceparent)

    def test_http_timeout_is_loaded_as_an_integer(self):
        with patch.dict(os.environ, {"DAGSHUB_HTTP_TIMEOUT": "12"}, clear=False):
            config = load_config_module()

        self.assertEqual(config.http_timeout, 12)
        self.assertIsInstance(config.http_timeout, int)
