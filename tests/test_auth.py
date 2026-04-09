import os
from openapi_cli_gen.engine.auth import build_auth_config
from openapi_cli_gen.spec.parser import SecuritySchemeInfo


def test_bearer_auth_from_env():
    schemes = [SecuritySchemeInfo(name="bearerAuth", type="http", scheme="bearer")]
    os.environ["TESTCLI_TOKEN"] = "secret-123"
    try:
        auth = build_auth_config("testcli", schemes)
        assert auth.get_headers() == {"Authorization": "Bearer secret-123"}
    finally:
        del os.environ["TESTCLI_TOKEN"]


def test_api_key_auth_from_env():
    schemes = [SecuritySchemeInfo(name="apiKey", type="apiKey", header_name="X-API-Key", location="header")]
    os.environ["TESTCLI_API_KEY"] = "key-456"
    try:
        auth = build_auth_config("testcli", schemes)
        assert auth.get_headers() == {"X-API-Key": "key-456"}
    finally:
        del os.environ["TESTCLI_API_KEY"]


def test_no_auth_when_no_env():
    schemes = [SecuritySchemeInfo(name="bearerAuth", type="http", scheme="bearer")]
    os.environ.pop("TESTCLI_TOKEN", None)
    auth = build_auth_config("testcli", schemes)
    assert auth.get_headers() == {}


def test_explicit_token_overrides_env():
    schemes = [SecuritySchemeInfo(name="bearerAuth", type="http", scheme="bearer")]
    os.environ["TESTCLI_TOKEN"] = "env-token"
    try:
        auth = build_auth_config("testcli", schemes)
        auth.set_token("explicit-token")
        assert auth.get_headers() == {"Authorization": "Bearer explicit-token"}
    finally:
        del os.environ["TESTCLI_TOKEN"]
