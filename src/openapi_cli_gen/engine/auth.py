from __future__ import annotations

import base64
import os

from openapi_cli_gen.spec.parser import SecuritySchemeInfo


class AuthState:
    """Holds resolved auth credentials and produces HTTP headers."""

    def __init__(self):
        self._headers: dict[str, str] = {}
        self._token_override: str | None = None
        self._scheme_type: str | None = None
        self._header_name: str | None = None

    def set_token(self, token: str) -> None:
        self._token_override = token

    def get_headers(self) -> dict[str, str]:
        if self._token_override:
            if self._scheme_type == "bearer":
                return {"Authorization": f"Bearer {self._token_override}"}
            elif self._scheme_type == "apiKey" and self._header_name:
                return {self._header_name: self._token_override}
        return dict(self._headers)


def build_auth_config(
    cli_name: str,
    schemes: list[SecuritySchemeInfo],
) -> AuthState:
    """Build auth state from security schemes + environment variables.

    Env var conventions (prefix = cli name, upper-cased, dashes to underscores):
        bearer token:   {PREFIX}_TOKEN
        apiKey header:  {PREFIX}_API_KEY
        http basic:     {PREFIX}_USERNAME + {PREFIX}_PASSWORD
    """
    prefix = cli_name.upper().replace("-", "_")
    state = AuthState()

    for scheme in schemes:
        # Normalize scheme name — RFC 6750 uses "Bearer" (capital), but OpenAPI specs
        # often use "bearer". Match case-insensitively so both work.
        scheme_name = (scheme.scheme or "").lower()
        if scheme.type == "http" and scheme_name == "bearer":
            state._scheme_type = "bearer"
            token = os.environ.get(f"{prefix}_TOKEN")
            if token:
                state._headers = {"Authorization": f"Bearer {token}"}
            break
        elif scheme.type == "http" and scheme_name == "basic":
            state._scheme_type = "basic"
            username = os.environ.get(f"{prefix}_USERNAME")
            password = os.environ.get(f"{prefix}_PASSWORD")
            if username is not None and password is not None:
                encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
                state._headers = {"Authorization": f"Basic {encoded}"}
            break
        elif scheme.type == "apiKey" and scheme.location == "header":
            state._scheme_type = "apiKey"
            state._header_name = scheme.header_name or "X-API-Key"
            api_key = os.environ.get(f"{prefix}_API_KEY")
            if api_key:
                state._headers = {state._header_name: api_key}
            break

    return state
