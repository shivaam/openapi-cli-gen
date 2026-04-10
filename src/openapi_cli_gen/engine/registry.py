from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from openapi_cli_gen.engine.models import schema_to_model, get_body_model, TYPE_MAP
from openapi_cli_gen.spec.parser import EndpointInfo


@dataclass
class CommandInfo:
    model: type[BaseModel]
    endpoint: EndpointInfo


def build_registry(
    endpoints: list[EndpointInfo],
    generated_models: dict[str, type[BaseModel]] | None = None,
) -> dict[str, dict[str, CommandInfo]]:
    """Build a command registry from parsed endpoints.

    Args:
        endpoints: Parsed endpoint list.
        generated_models: Pre-generated models from datamodel-code-generator (optional).

    Returns: {group_name: {command_name: CommandInfo}}
    """
    registry: dict[str, dict[str, CommandInfo]] = {}
    model_cache: dict[str, type[BaseModel]] = {}
    gen_models = generated_models or {}

    for ep in endpoints:
        group = ep.tag
        cmd_name = _derive_command_name(ep)
        model = _build_command_model(ep, model_cache, gen_models)

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
    generated_models: dict[str, type[BaseModel]],
) -> type[BaseModel]:
    """Build a dynamic Pydantic model combining params + body fields."""
    from typing import Any

    fields: dict[str, Any] = {}

    from openapi_cli_gen.engine.models import to_snake_case

    # Path params → required fields (snake_cased for CLI, original name kept as alias)
    for p in ep.path_params:
        py_type = TYPE_MAP.get(p.type, str)
        snake_name = to_snake_case(p.name)
        field_info = FieldInfo(description=p.name)
        if snake_name != p.name:
            # Keep the original name as serialization_alias for URL substitution
            field_info = FieldInfo(description=p.name, serialization_alias=p.name)
        fields[snake_name] = (py_type, field_info)

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
        snake_name = to_snake_case(p.name)
        if snake_name != p.name:
            fields[snake_name] = (py_type, FieldInfo(default=default, serialization_alias=p.name))
        else:
            fields[p.name] = (py_type, FieldInfo(default=default))

    # Body schema → try generated models first, fall back to simple builder
    if ep.body_schema:
        # Prefer the original $ref name if available (preserves allOf/oneOf handling)
        schema_name = ep.body_ref_name or _extract_schema_name(ep.body_schema)
        body_model = get_body_model(schema_name, generated_models, ep.body_schema, model_cache)
        # Replace complex union types with str to keep CLI permissive.
        # Users can pass JSON strings that our builder will parse before sending.
        # Generated models from datamodel-code-generator preserve exact types
        # (e.g., VectorParams | Record) which pydantic-settings can't flag-ify.
        for fname, finfo in body_model.model_fields.items():
            annotation = finfo.annotation
            # Fall back to str for complex types that pydantic-settings can't flag-ify.
            # User passes JSON which our builder parses before sending.
            if (_is_complex_union(annotation)
                or _is_list_of_basemodel(annotation)
                or _is_root_or_problematic_basemodel(annotation)):
                # Drop the default entirely — it may not be a valid string
                new_info = FieldInfo(default=None, description=finfo.description)
                fields[fname] = (str | None, new_info)
                continue

            # Strip alias so pydantic-settings uses the Python field name (snake_case)
            # for CLI flags. Keep serialization_alias so JSON body uses original name.
            # datamodel-code-generator sets alias=original_name which pydantic-settings
            # uses as the CLI flag, giving camelCase flags instead of kebab-case.
            if finfo.alias and finfo.alias != fname:
                new_info = FieldInfo(
                    default=finfo.default,
                    description=finfo.description,
                    serialization_alias=finfo.alias,  # Keep original name for JSON output
                )
                fields[fname] = (annotation, new_info)
            else:
                fields[fname] = (annotation, finfo)

    # Add output_format flag to every command
    fields["output_format"] = (str, FieldInfo(default="json", description="Output format: json, table, yaml, raw"))

    model_name = f"Cmd_{ep.operation_id}"
    return create_model(model_name, __doc__=ep.summary or ep.operation_id, **fields)


def _is_complex_union(annotation) -> bool:
    """Check if a type annotation is a union with 2+ BaseModel members.

    These can't be flag-ified — pydantic-settings can't pick a variant.
    Returns True for `VectorParams | Record | None`.
    """
    from typing import get_args, get_origin, Union
    from types import UnionType

    origin = get_origin(annotation)
    if origin is not Union and not isinstance(annotation, UnionType):
        return False

    args = get_args(annotation)
    non_none = [a for a in args if a is not type(None)]

    if len(non_none) <= 1:
        return False

    base_model_count = 0
    for arg in non_none:
        try:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                base_model_count += 1
        except TypeError:
            pass
    return base_model_count >= 2


def _is_root_or_problematic_basemodel(annotation) -> bool:
    """Check if annotation is a BaseModel (possibly Optional) that should be
    CLI-friendly str instead of nested flag expansion.

    pydantic-settings struggles with:
    - RootModel subclasses (they wrap a single type)
    - Models with complex field types
    Returns True if we should fall back to accepting a JSON string.
    """
    from typing import get_args, get_origin, Union
    from types import UnionType

    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            annotation = args[0]
        else:
            return False  # complex union handled elsewhere

    try:
        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            return False
    except TypeError:
        return False

    # RootModel — always fall back (not flag-friendly)
    try:
        from pydantic import RootModel
        if issubclass(annotation, RootModel):
            return True
    except ImportError:
        pass

    # Check if any field has a complex type that pydantic-settings can't handle
    for name, info in annotation.model_fields.items():
        if _is_complex_union(info.annotation) or _is_list_of_basemodel(info.annotation):
            return True

    return False


def _is_list_of_basemodel(annotation) -> bool:
    """Check if annotation is `list[BaseModel]` or `list[BaseModel] | None`."""
    from typing import get_args, get_origin, Union
    from types import UnionType

    # Unwrap Optional
    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            annotation = args[0]
            origin = get_origin(annotation)

    if origin is not list:
        return False

    item_type = get_args(annotation)[0] if get_args(annotation) else None
    if item_type is None:
        return False
    try:
        return isinstance(item_type, type) and issubclass(item_type, BaseModel)
    except TypeError:
        return False


def _extract_schema_name(schema: dict) -> str:
    """Extract a model name from a body schema dict.

    Looks for title, $ref fragment, or generates a fallback name.
    """
    if "title" in schema:
        return schema["title"]
    # After jsonref resolution, the original $ref is lost, but the schema
    # might still have a recognizable structure. Use properties as key.
    props = list(schema.get("properties", {}).keys())
    if props:
        return "".join(p.title() for p in props[:3]) + "Body"
    return "InlineBody"
