from __future__ import annotations

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
    """Build auth state from security schemes + environment variables."""
    prefix = cli_name.upper().replace("-", "_")
    state = AuthState()

    for scheme in schemes:
        if scheme.type == "http" and scheme.scheme == "bearer":
            state._scheme_type = "bearer"
            token = os.environ.get(f"{prefix}_TOKEN")
            if token:
                state._headers = {"Authorization": f"Bearer {token}"}
            break
        elif scheme.type == "apiKey" and scheme.location == "header":
            state._scheme_type = "apiKey"
            state._header_name = scheme.header_name or "X-API-Key"
            api_key = os.environ.get(f"{prefix}_API_KEY")
            if api_key:
                state._headers = {state._header_name: api_key}
            break

    return state
