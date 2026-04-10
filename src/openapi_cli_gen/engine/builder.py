from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

import httpx

from openapi_cli_gen.spec.loader import load_spec, load_raw_spec, extract_body_schema_names
from openapi_cli_gen.spec.parser import parse_spec, extract_security_schemes
from openapi_cli_gen.engine.models import generate_models_from_spec
from openapi_cli_gen.engine.registry import build_registry, CommandInfo
from openapi_cli_gen.engine.dispatch import dispatch
from openapi_cli_gen.engine.auth import build_auth_config
from openapi_cli_gen.output.formatter import format_output


def build_cli(
    spec: str | Path,
    name: str = "cli",
    base_url: str | None = None,
) -> Callable:
    """Build a CLI application from an OpenAPI spec.

    Args:
        spec: Path to OpenAPI spec file or URL.
        name: CLI name (used for help text and env var prefix).
        base_url: Override the API base URL. If None, uses first server from spec.

    Returns:
        A callable that accepts a list of args (or uses sys.argv[1:]).
    """
    spec_path = str(spec)
    resolved = load_spec(spec_path)
    raw = load_raw_spec(spec_path)
    body_ref_names = extract_body_schema_names(raw)
    endpoints = parse_spec(resolved, body_ref_names=body_ref_names)
    security_schemes = extract_security_schemes(resolved)

    # Generate models from spec (uses datamodel-code-generator with disk caching)
    # Works for both local files and URLs
    generated_models = generate_models_from_spec(spec_path)

    registry = build_registry(endpoints, generated_models=generated_models)
    auth_state = build_auth_config(name, security_schemes)

    if base_url is None:
        servers = resolved.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost:8000"

    # Attach cli_cmd to each command model
    for group_cmds in registry.values():
        for cmd_info in group_cmds.values():
            _attach_cli_cmd(cmd_info, base_url, auth_state)

    def app(args: list[str] | None = None):
        if args is None:
            args = sys.argv[1:]
        dispatch(registry, args, name=name)

    return app


def _attach_cli_cmd(cmd_info: CommandInfo, base_url: str, auth_state) -> None:
    """Attach a cli_cmd method to the command model that makes the HTTP call."""
    ep = cmd_info.endpoint

    def cli_cmd(self):
        import enum
        from pydantic_core import PydanticUndefined

        data = self.model_dump(exclude_none=True, by_alias=True, mode="json")

        # Remove fields that equal their default value (serialized form).
        # pydantic-settings always sets all fields (from defaults), so exclude_unset
        # doesn't work. We compare serialized values against the serialized default
        # to drop unintended defaults that some APIs reject.
        model_cls = type(self)
        alias_to_default = {}
        for name, info in model_cls.model_fields.items():
            if info.default is PydanticUndefined or info.default is None:
                continue
            default_val = info.default
            if isinstance(default_val, enum.Enum):
                default_val = default_val.value
            key = info.alias or info.serialization_alias or name
            alias_to_default[key] = default_val
        data = {k: v for k, v in data.items() if k not in alias_to_default or v != alias_to_default[k]}

        # Extract output format if present
        output_fmt = data.pop("output_format", "json")

        # Separate path params from body/query
        path_names = {p.name for p in ep.path_params}
        query_names = {p.name for p in ep.query_params}

        path_params = {k: v for k, v in data.items() if k in path_names}
        query_params = {k: v for k, v in data.items() if k in query_names}
        # For body: exclude query params and path params UNLESS the body schema
        # explicitly defines that field (some APIs need id in both path and body)
        body_field_names = set()
        if ep.body_schema:
            body_field_names = set(ep.body_schema.get("properties", {}).keys())
        exclude_from_body = (path_names - body_field_names) | query_names
        body = {k: v for k, v in data.items() if k not in exclude_from_body}

        # Handle nested models: convert Pydantic models to dicts for JSON serialization
        body = _serialize_body(body)

        # Parse JSON strings: if a field value looks like JSON (starts with { or [),
        # parse it so nested objects/arrays are sent correctly to the API
        body = _parse_json_strings(body)

        # Unwrap RootModel: if body has only one field named 'root', send its value directly.
        # This handles cases where the request body is a RootModel wrapping a single union.
        if set(body.keys()) == {"root"}:
            body = body["root"]

        # Build URL with path params
        path = ep.path
        for k, v in path_params.items():
            path = path.replace(f"{{{k}}}", str(v))
        url = f"{base_url}{path}"

        headers = auth_state.get_headers()

        with httpx.Client(timeout=300) as client:
            if ep.method in ("post", "put", "patch"):
                # For POST/PUT/PATCH: always send a JSON body (even empty {}) if the
                # endpoint declares a body schema, otherwise APIs like Qdrant reject
                # the request with "EOF while parsing JSON body".
                json_body = body
                if not json_body and ep.body_schema is not None:
                    json_body = {}
                elif not json_body:
                    json_body = None
                resp = client.request(ep.method.upper(), url, json=json_body, params=query_params, headers=headers)
            else:
                resp = client.request(ep.method.upper(), url, params=query_params, headers=headers)

        if resp.status_code >= 400:
            print(f"Error: {resp.status_code}")
            try:
                print(format_output(resp.json(), "json"))
            except Exception:
                print(resp.text)
            raise SystemExit(1)

        # Handle 204 No Content (successful DELETE)
        if resp.status_code == 204 or not resp.text:
            print("Success (no content)")
            return

        try:
            result = resp.json()
        except Exception:
            result = resp.text

        output = format_output(result, output_fmt)
        if output is not None:
            print(output)

    cmd_info.model.cli_cmd = cli_cmd


def _parse_json_strings(obj):
    """Recursively parse string values that look like JSON (start with { or [).

    This lets users pass nested objects/arrays as JSON strings on the CLI:
        --vectors '{"size": 4, "distance": "Cosine"}'
    Without this, the string would be sent as-is instead of a parsed object.
    """
    if isinstance(obj, dict):
        return {k: _parse_json_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_parse_json_strings(v) for v in obj]
    if isinstance(obj, str):
        stripped = obj.strip()
        if stripped.startswith(("{", "[")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return obj
        return obj
    return obj


def _serialize_body(body: dict) -> dict:
    """Recursively convert Pydantic models and enums in body to JSON-serializable dicts."""
    from enum import Enum
    from pydantic import BaseModel

    result = {}
    for k, v in body.items():
        if isinstance(v, BaseModel):
            result[k] = v.model_dump(exclude_none=True)
        elif isinstance(v, Enum):
            result[k] = v.value
        elif isinstance(v, dict):
            result[k] = _serialize_body(v)
        elif isinstance(v, list):
            result[k] = [
                item.model_dump(exclude_none=True) if isinstance(item, BaseModel)
                else item.value if isinstance(item, Enum)
                else item
                for item in v
            ]
        else:
            result[k] = v
    return result


def build_command_group(
    spec: str | Path,
    name: str = "api",
    base_url: str | None = None,
) -> dict[str, dict[str, CommandInfo]]:
    """Build command group from spec. Returns the registry for programmatic use."""
    spec_path = str(spec)
    resolved = load_spec(spec_path)
    raw = load_raw_spec(spec_path)
    body_ref_names = extract_body_schema_names(raw)
    endpoints = parse_spec(resolved, body_ref_names=body_ref_names)
    security_schemes = extract_security_schemes(resolved)

    generated_models = {}
    if not spec_path.startswith(("http://", "https://")):
        generated_models = generate_models_from_spec(spec_path)

    registry = build_registry(endpoints, generated_models=generated_models)
    auth_state = build_auth_config(name, security_schemes)

    if base_url is None:
        servers = resolved.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost:8000"

    for group_cmds in registry.values():
        for cmd_info in group_cmds.values():
            _attach_cli_cmd(cmd_info, base_url, auth_state)

    return registry
