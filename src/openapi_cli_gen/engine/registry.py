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
        group = _normalize_group_name(ep.tag)
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


def _clean_nested_model_descriptions(model_cls: type[BaseModel], _seen: set | None = None) -> None:
    """Recursively strip markdown from descriptions on a BaseModel and its nested fields.

    pydantic-settings reads field descriptions from nested BaseModels directly when
    rendering --help. A one-level clean on the command model is not enough — we need
    to walk into every nested BaseModel field and clean theirs too.

    Mutates the model classes in place. Safe because (a) descriptions are purely
    cosmetic, (b) we only strip markdown which is strictly better, and (c) the
    transformation is idempotent.
    """
    if _seen is None:
        _seen = set()
    if model_cls in _seen:
        return
    _seen.add(model_cls)

    try:
        fields = model_cls.model_fields
    except AttributeError:
        return

    for fname, finfo in list(fields.items()):
        original = finfo.description
        cleaned = _clean_description(original)
        if cleaned != original:
            finfo.description = cleaned
        # Walk into nested BaseModel types (including Optional[Model], list[Model], union members)
        from typing import get_args, get_origin, Union
        from types import UnionType
        anno = finfo.annotation
        to_check = [anno]
        # Unwrap container types
        for _ in range(3):  # limit recursion depth on nested containers
            new_to_check = []
            for t in to_check:
                origin = get_origin(t)
                if origin is Union or isinstance(t, UnionType) or origin in (list, tuple, set, frozenset, dict):
                    new_to_check.extend(get_args(t))
                else:
                    new_to_check.append(t)
            to_check = new_to_check
        for t in to_check:
            try:
                if isinstance(t, type) and issubclass(t, BaseModel) and t is not BaseModel:
                    _clean_nested_model_descriptions(t, _seen)
            except TypeError:
                pass


def _clean_description(desc: str | None) -> str | None:
    """Strip Markdown syntax from OpenAPI `description` fields so argparse
    `--help` output doesn't render things like `**bold**` or
    `[Responses](/docs/api-reference/responses)` verbatim.

    Keeps the text, drops the formatting. Truncates to a reasonable length
    for CLI help rendering (argparse prints the full string if left unchecked).
    """
    if not desc:
        return desc
    s = str(desc)
    # Strip `[text](url)` → `text`
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # Strip `**bold**`, `__bold__`, `*em*`, `_em_`
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)
    s = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"\1", s)
    # Strip inline code `…`
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # Strip headings `# Foo` (leading `#`s on a line)
    s = re.sub(r"(?m)^\s*#+\s*", "", s)
    # Collapse multiple whitespace/newlines into single spaces
    s = re.sub(r"\s+", " ", s).strip()
    # Truncate overly long descriptions — argparse help gets unreadable past ~300 chars
    if len(s) > 300:
        s = s[:297].rstrip() + "..."
    return s


def _normalize_group_name(tag: str) -> str:
    """Normalize an OpenAPI tag into a shell-friendly command group name.

    Tags in the wild include "Vector stores", "Users (admin)", "Database Backups
    (admin)", "Facet Search" — each of which requires shell quoting (or fails
    outright on shells that interpret parens). Normalize to a plain kebab-case
    identifier that never needs quoting:

        "Vector stores"           → "vector-stores"
        "Users (admin)"           → "users-admin"
        "Database Backups (admin)" → "database-backups-admin"
        "Facet Search"            → "facet-search"
        "API keys"                → "api-keys"
        "Fine-tuning"             → "fine-tuning"   (already fine)
        "Health"                  → "health"
    """
    if not tag:
        return "default"
    # Drop parentheses and brackets entirely (keeping their contents)
    normalized = re.sub(r"[()\[\]{}]", " ", tag)
    # Collapse whitespace to single spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    # Replace spaces and underscores with hyphens
    normalized = re.sub(r"[\s_]+", "-", normalized)
    # Lowercase
    normalized = normalized.lower()
    # Drop any remaining non-alphanumeric-or-hyphen chars
    normalized = re.sub(r"[^a-z0-9\-]", "", normalized)
    # Collapse multiple hyphens
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "default"


HTTP_VERBS_PREFIX = ("delete", "update", "create", "patch", "put", "post", "get",
                     "list", "add", "find", "place", "send", "upload", "trigger",
                     "download", "search", "check", "run", "cancel", "reset",
                     "fetch", "retrieve", "remove")


def _split_leading_verb(normalized: str) -> str:
    """Insert an underscore after a leading HTTP verb that's jammed against the
    resource name, so `deletechat` → `delete_chat`, `patchembedders` →
    `patch_embedders`, `deletedisplayed_attributes` → `delete_displayed_attributes`.

    Some OpenAPI specs (Meilisearch's Settings group is the poster child) don't
    separate the verb from the resource in operationIds. Without this split, our
    kebab converter emits `deletechat` which is unreadable.

    Already-separated names (`list_users`, `delete_user`) pass through unchanged.
    """
    if "_" in normalized[:6]:
        # Already has a separator in the first few chars — leave it alone.
        return normalized
    for verb in HTTP_VERBS_PREFIX:
        if normalized.startswith(verb) and len(normalized) > len(verb):
            rest = normalized[len(verb):]
            # Only split if the rest starts with a letter (not a digit or underscore)
            if rest[0].isalpha():
                return f"{verb}_{rest}"
    return normalized


def _derive_command_name(ep: EndpointInfo) -> str:
    """Derive a CLI command name from an endpoint.

    Handles both snake_case (list_users) and camelCase (addPet) operationIds.
    Strategy: normalize to snake_case, split leading HTTP verb if jammed against
    the resource name, strip tag suffix/prefix, kebab-case result.

    Examples:
        list_users (tag=users) → list
        create_user (tag=users) → create
        addPet (tag=pet) → add
        findPetsByStatus (tag=pet) → find-by-status
        getPetById (tag=pet) → get-by-id
        uploadFile (tag=pet) → upload-file
        deletechat (tag=Settings) → delete-chat
        patchembedders (tag=Settings) → patch-embedders
        deletedisplayedAttributes (tag=Settings) → delete-displayed-attributes
    """
    op_id = ep.operation_id
    tag = ep.tag

    # Normalize camelCase to snake_case first
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", op_id).lower()

    # Split leading HTTP verb if concatenated against the resource name (Meili case).
    normalized = _split_leading_verb(normalized)

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

    # Query params → ALWAYS optional fields with default=None.
    #
    # Rationale: several popular APIs (Meilisearch, others) over-declare `required: true`
    # on query parameters that are actually optional at runtime. Enforcing required at the
    # CLI layer forces users to pass dummy values they don't care about. Servers will still
    # reject truly-required missing params with a clear HTTP 400, which is a better error
    # than pydantic-settings' "field required" complaint.
    #
    # Also: object-typed query params (style=form, explode=true, schema: object with
    # properties) flatten into individual query params per property, matching how the
    # wire actually works. Typesense's `searchParameters` is the canonical example —
    # the spec declares one object-typed query param, but the server takes each property
    # as a separate `?key=value` pair.
    for p in ep.query_params:
        py_type = TYPE_MAP.get(p.type, str)
        py_type = py_type | None  # always optional at CLI layer
        default = p.default
        # Guard: skip defaults that don't match the type (e.g., list default for string field)
        if default is not None and not isinstance(default, (str, int, float, bool)):
            default = None
        if default is None:
            default = None  # explicit
        snake_name = to_snake_case(p.name)
        if snake_name != p.name:
            fields[snake_name] = (py_type, FieldInfo(default=default, serialization_alias=p.name))
        else:
            fields[p.name] = (py_type, FieldInfo(default=default))

    # Body schema → try generated models first, fall back to simple builder.
    #
    # All body fields are forced to be CLI-optional (even if the spec marks them
    # `required: true`). Rationale: we always expose a `--root` JSON escape hatch
    # for bodies, and pydantic-settings validates required fields at flag-parse
    # time — before our cli_cmd runs — so enforcing required would make --root
    # unusable. Users who miss a required field get a clear HTTP error from the
    # server instead of a CLI-layer "field required" error.
    from pydantic_core import PydanticUndefined as _Undef
    # Note: `is not None` matters here — Meilisearch declares some body schemas as
    # literal `{}` (empty dict) which is falsy. Those still need the --root flag.
    if ep.body_schema is not None:
        # Prefer the original $ref name if available (preserves allOf/oneOf handling)
        schema_name = ep.body_ref_name or _extract_schema_name(ep.body_schema)
        if ep.body_content_type == "multipart/form-data":
            # Bypass datamodel-code-generator for multipart — dcg types binary
            # fields as `bytes` which pydantic-settings can't flag-ify. The simple
            # builder maps type:string (any format) → str, so users can pass paths.
            from openapi_cli_gen.engine.models import schema_to_model
            body_model = schema_to_model(schema_name, ep.body_schema, _model_cache=model_cache)
        else:
            body_model = get_body_model(schema_name, generated_models, ep.body_schema, model_cache)
        # Replace complex union types with str to keep CLI permissive.
        # Users can pass JSON strings that our builder will parse before sending.
        # Generated models from datamodel-code-generator preserve exact types
        # (e.g., VectorParams | Record) which pydantic-settings can't flag-ify.
        for fname, finfo in body_model.model_fields.items():
            # Strip markdown from upstream description fields so argparse --help
            # doesn't render raw **bold** or [link](url) text.
            cleaned_desc = _clean_description(finfo.description)
            annotation = finfo.annotation
            # Fall back to str for complex types that pydantic-settings can't flag-ify.
            # User passes JSON which our builder parses before sending.
            if (_is_complex_union(annotation)
                or _is_list_of_basemodel(annotation)
                or _is_root_or_problematic_basemodel(annotation)):
                # Drop the default entirely — it may not be a valid string
                new_info = FieldInfo(default=None, description=cleaned_desc)
                fields[fname] = (str | None, new_info)
                continue

            # Force CLI-optional: make annotation Optional and set default to None
            # if the field was originally required (no default). This lets --root
            # bypass typed flags without tripping pydantic-settings' required check.
            is_required = finfo.default is _Undef
            if is_required:
                # Union with None to make it optional in pydantic's eyes
                annotation = annotation | None
                new_default = None
            else:
                new_default = finfo.default

            # Strip alias so pydantic-settings uses the Python field name (snake_case)
            # for CLI flags. Keep serialization_alias so JSON body uses original name.
            # datamodel-code-generator sets alias=original_name which pydantic-settings
            # uses as the CLI flag, giving camelCase flags instead of kebab-case.
            #
            # Determine the serialization_alias to preserve (either from dcg's
            # `alias` field or from the simple builder's existing `serialization_alias`).
            existing_ser_alias = None
            if finfo.alias and finfo.alias != fname:
                existing_ser_alias = finfo.alias
            elif finfo.serialization_alias and finfo.serialization_alias != fname:
                existing_ser_alias = finfo.serialization_alias

            if existing_ser_alias is not None:
                new_info = FieldInfo(
                    default=new_default,
                    description=cleaned_desc,
                    serialization_alias=existing_ser_alias,
                )
                fields[fname] = (annotation, new_info)
            elif is_required:
                new_info = FieldInfo(default=new_default, description=cleaned_desc)
                fields[fname] = (annotation, new_info)
            elif cleaned_desc != finfo.description:
                # Description had markdown — rebuild FieldInfo to replace it
                new_info = FieldInfo(default=finfo.default, description=cleaned_desc)
                fields[fname] = (annotation, new_info)
            else:
                fields[fname] = (annotation, finfo)

    # Universal --root escape hatch for JSON bodies.
    #
    # For every endpoint that declares a non-multipart request body, add a `--root`
    # flag that accepts a raw JSON string. When provided, the builder uses it as the
    # entire request body, bypassing typed flags. This handles three critical cases:
    #
    #   1. Endpoints with schemaless `type: object` bodies (Typesense documents/index,
    #      Meilisearch Documents/replace) that produce zero typed flags.
    #   2. Endpoints where the spec's field casing doesn't match the server's wire
    #      format (Meilisearch's SearchQuery declares snake_case, server wants camelCase).
    #   3. Any endpoint where users want to paste a JSON payload instead of building
    #      it up flag by flag.
    #
    # We only add `root` if no field named `root` already exists (RootModel case
    # already has one).
    if ep.body_schema is not None and ep.body_content_type != "multipart/form-data":
        if "root" not in fields:
            fields["root"] = (
                str | None,
                FieldInfo(
                    default=None,
                    description="Pass the entire request body as a JSON string (overrides typed flags).",
                ),
            )

    # Add output_format flag to every command
    fields["output_format"] = (str, FieldInfo(default="json", description="Output format: json, table, yaml, raw"))

    model_name = f"Cmd_{ep.operation_id}"
    doc = _clean_description(ep.summary) or ep.operation_id
    built = create_model(model_name, __doc__=doc, **fields)
    # Walk nested BaseModel types and clean their field descriptions too —
    # pydantic-settings reads nested descriptions directly for --help, so a
    # top-level clean alone leaves markdown in nested flags like
    # --stream-options.include-usage.
    _clean_nested_model_descriptions(built)
    return built


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
