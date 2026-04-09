from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from openapi_cli_gen.engine.models import schema_to_model, TYPE_MAP
from openapi_cli_gen.spec.parser import EndpointInfo


@dataclass
class CommandInfo:
    model: type[BaseModel]
    endpoint: EndpointInfo


def build_registry(
    endpoints: list[EndpointInfo],
) -> dict[str, dict[str, CommandInfo]]:
    """Build a command registry from parsed endpoints.

    Returns: {group_name: {command_name: CommandInfo}}
    """
    registry: dict[str, dict[str, CommandInfo]] = {}
    model_cache: dict[str, type[BaseModel]] = {}

    for ep in endpoints:
        group = ep.tag
        cmd_name = _derive_command_name(ep)
        model = _build_command_model(ep, model_cache)

        registry.setdefault(group, {})[cmd_name] = CommandInfo(
            model=model,
            endpoint=ep,
        )

    return registry


def _derive_command_name(ep: EndpointInfo) -> str:
    """Derive a CLI command name from an endpoint.

    Strategy: strip the tag suffix (singular or plural) from operationId, kebab-case the rest.
    Examples: list_users → list, create_user → create, get_user → get
    """
    op_id = ep.operation_id
    tag = ep.tag

    # Build variants of the tag to try stripping from the end of op_id
    # e.g. tag="users" → try "_users", "_user"
    # e.g. tag="companies" → try "_companies", "_company", "_companie"
    singular = tag.rstrip("s") if tag.endswith("s") else tag
    suffixes_to_try = [f"_{tag}", f"_{singular}", f"_{tag}s"]

    for suffix in suffixes_to_try:
        if op_id.endswith(suffix):
            remainder = op_id[: -len(suffix)]
            if remainder:
                return _to_kebab(remainder)

    # Try stripping tag as a prefix (e.g. users_list → list)
    for prefix in [f"{tag}_", f"{singular}_"]:
        if op_id.startswith(prefix):
            remainder = op_id[len(prefix):]
            if remainder:
                return _to_kebab(remainder)

    # Try extracting just the leading verb if nothing else matched
    for verb in ("list", "get", "create", "update", "delete", "patch", "send", "trigger"):
        if op_id.startswith(f"{verb}_") or op_id == verb:
            return verb

    return _to_kebab(op_id)


def _to_kebab(name: str) -> str:
    """Convert snake_case or camelCase to kebab-case."""
    name = name.replace("_", "-")
    name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name).lower()
    return name


def _build_command_model(
    ep: EndpointInfo,
    model_cache: dict[str, type[BaseModel]],
) -> type[BaseModel]:
    """Build a dynamic Pydantic model combining params + body fields."""
    from typing import Any

    fields: dict[str, Any] = {}

    # Path params → required fields
    for p in ep.path_params:
        py_type = TYPE_MAP.get(p.type, str)
        fields[p.name] = (py_type, FieldInfo(description=p.name))

    # Query params → optional fields with defaults
    for p in ep.query_params:
        py_type = TYPE_MAP.get(p.type, str)
        if not p.required:
            py_type = py_type | None
        default = p.default if p.default is not None else (None if not p.required else ...)
        fields[p.name] = (py_type, FieldInfo(default=default))

    # Body schema → merge fields from schema_to_model
    if ep.body_schema:
        body_model = schema_to_model(
            f"{ep.tag.title()}{ep.operation_id.title().replace('_', '')}Body",
            ep.body_schema,
            doc=ep.summary,
            _model_cache=model_cache,
        )
        for fname, finfo in body_model.model_fields.items():
            fields[fname] = (finfo.annotation, finfo)

    model_name = f"Cmd_{ep.operation_id}"
    return create_model(model_name, __doc__=ep.summary or ep.operation_id, **fields)
