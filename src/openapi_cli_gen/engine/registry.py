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

        # Handle name collisions: if command name already exists in group,
        # use the full operationId as kebab-case fallback
        group_cmds = registry.setdefault(group, {})
        if cmd_name in group_cmds:
            # Rename the existing one too if it hasn't been renamed yet
            existing = group_cmds[cmd_name]
            existing_full = _to_kebab(re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", existing.endpoint.operation_id).lower())
            if existing_full != cmd_name:
                group_cmds[existing_full] = existing
                del group_cmds[cmd_name]
            cmd_name = _to_kebab(re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", ep.operation_id).lower())

        group_cmds[cmd_name] = CommandInfo(
            model=model,
            endpoint=ep,
        )

    return registry


def _derive_command_name(ep: EndpointInfo) -> str:
    """Derive a CLI command name from an endpoint.

    Handles both snake_case (list_users) and camelCase (addPet) operationIds.
    Strategy: normalize to snake_case, strip tag suffix/prefix, kebab-case result.

    Examples:
        list_users (tag=users) → list
        create_user (tag=users) → create
        addPet (tag=pet) → add
        findPetsByStatus (tag=pet) → find-by-status
        getPetById (tag=pet) → get-by-id
        uploadFile (tag=pet) → upload-file
    """
    op_id = ep.operation_id
    tag = ep.tag

    # Normalize camelCase to snake_case first
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", op_id).lower()

    singular = tag.rstrip("s") if tag.endswith("s") else tag
    tag_lower = tag.lower()
    singular_lower = singular.lower()

    # Try stripping tag variants from the end
    for suffix in [f"_{tag_lower}", f"_{singular_lower}", f"_{tag_lower}s"]:
        if normalized.endswith(suffix):
            remainder = normalized[: -len(suffix)]
            if remainder:
                return _to_kebab(remainder)

    # Try stripping tag from the middle (e.g., find_pets_by_status → find_by_status)
    for tag_word in [f"_{tag_lower}_", f"_{singular_lower}_", f"_{tag_lower}s_"]:
        if tag_word in normalized:
            remainder = normalized.replace(tag_word, "_", 1)
            return _to_kebab(remainder)

    # Try stripping tag as prefix
    for prefix in [f"{tag_lower}_", f"{singular_lower}_"]:
        if normalized.startswith(prefix):
            remainder = normalized[len(prefix):]
            if remainder:
                return _to_kebab(remainder)

    # Try extracting just the leading verb
    for verb in ("list", "get", "create", "update", "delete", "patch", "send", "trigger",
                 "add", "find", "place", "upload"):
        if normalized.startswith(f"{verb}_") or normalized == verb:
            return verb if normalized == verb else _to_kebab(normalized)

    return _to_kebab(normalized)


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
        default = p.default
        # Guard: skip defaults that don't match the type (e.g., list default for string field)
        if default is not None and not isinstance(default, (str, int, float, bool)):
            default = None
        if default is None and not p.required:
            default = None
        elif default is None and p.required:
            default = ...
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

    # Add output_format flag to every command
    fields["output_format"] = (str, FieldInfo(default="json", description="Output format: json, table, yaml, raw"))

    model_name = f"Cmd_{ep.operation_id}"
    return create_model(model_name, __doc__=ep.summary or ep.operation_id, **fields)
