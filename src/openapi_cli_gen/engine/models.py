"""Dynamic Pydantic model generation from OpenAPI specs.

Uses datamodel-code-generator for robust schema handling (allOf, oneOf, anyOf,
nullable, enums, recursive schemas, etc.) with disk caching for fast startup.

Falls back to a simple built-in builder if datamodel-code-generator is not available.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}

CACHE_DIR = Path.home() / ".cache" / "openapi-cli-gen" / "models"


def to_snake_case(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def generate_models_from_spec(spec_path: str) -> dict[str, type[BaseModel]]:
    """Generate all Pydantic models from an OpenAPI spec file or URL.

    Uses datamodel-code-generator with disk caching.
    First call: ~300ms (generate + cache). Subsequent calls: ~50ms (import from cache).

    Returns: dict mapping model class names to model classes.
    """
    # Handle URL specs: download to a temp file
    if spec_path.startswith(("http://", "https://")):
        import httpx
        try:
            resp = httpx.get(spec_path, follow_redirects=True, timeout=30)
            resp.raise_for_status()
        except Exception:
            return {}

        content = resp.text
        spec_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # Write spec to cache dir with a predictable name based on hash
        suffix = ".yaml" if spec_path.endswith((".yaml", ".yml")) else ".json"
        spec_cache = CACHE_DIR / f"spec_{spec_hash}{suffix}"
        if not spec_cache.exists():
            spec_cache.write_text(content)
        cache_file = CACHE_DIR / f"models_{spec_hash}.py"

        if not cache_file.exists():
            _generate_and_cache(spec_cache, cache_file)

        return _load_from_cache(cache_file)

    path = Path(spec_path)
    if not path.exists():
        return {}

    # Cache key = hash of spec content
    spec_hash = hashlib.md5(path.read_bytes()).hexdigest()[:16]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"models_{spec_hash}.py"

    if not cache_file.exists():
        _generate_and_cache(path, cache_file)

    return _load_from_cache(cache_file)


def _generate_and_cache(spec_path: Path, cache_file: Path) -> None:
    """Generate models using datamodel-code-generator and save to cache."""
    try:
        from datamodel_code_generator import generate, InputFileType, DataModelType

        code = generate(
            input_=spec_path,
            input_file_type=InputFileType.OpenAPI,
            output_model_type=DataModelType.PydanticV2BaseModel,
            use_annotated=True,
            field_constraints=True,
            formatters=[],  # skip black/isort — we exec(), don't need pretty code
        )
        # Strip future annotations so pydantic-settings can resolve types for CLI flags
        code = code.replace("from __future__ import annotations\n", "")
        # Strip `discriminator='xxx'` from Field() calls. OpenAI has unions with
        # ambiguous discriminator values (two variants both with type='message') that
        # pydantic rejects. Without discriminator, pydantic tries each variant in order.
        import re
        # Pattern 1: `Field(discriminator='type')` → `Field()`
        code = re.sub(r"Field\(discriminator=['\"][^'\"]*['\"]\)", "Field()", code)
        # Pattern 2: `, discriminator='type'` → `` (inside Field with other args)
        code = re.sub(r",\s*discriminator=['\"][^'\"]*['\"]", "", code)
        # Pattern 3: `discriminator='type',` → `` (at start of Field args)
        code = re.sub(r"discriminator=['\"][^'\"]*['\"]\s*,\s*", "", code)
        cache_file.write_text(code)
    except ImportError:
        # datamodel-code-generator not installed — write empty module
        cache_file.write_text("# datamodel-code-generator not available\n")
    except Exception as e:
        # Generation failed — write empty module with error comment
        cache_file.write_text(f"# Generation failed: {e}\n")


def _load_from_cache(cache_file: Path) -> dict[str, type[BaseModel]]:
    """Load generated models from a cached Python file."""
    module_name = f"openapi_cli_gen._cached.{cache_file.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(cache_file))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return {
        name: obj
        for name, obj in vars(module).items()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
    }


def get_body_model(
    schema_name: str,
    generated_models: dict[str, type[BaseModel]],
    body_schema: dict,
    model_cache: dict[str, type[BaseModel]],
) -> type[BaseModel]:
    """Get a body model — prefer datamodel-code-generator models, fall back to simple builder.

    Args:
        schema_name: The expected model name (e.g., 'UserCreate').
        generated_models: Models from datamodel-code-generator (may be empty).
        body_schema: Raw JSON Schema dict for fallback.
        model_cache: Cache for fallback builder.
    """
    # Try to find in generated models (handles allOf, oneOf, etc. correctly)
    if generated_models:
        # Try exact match first
        if schema_name in generated_models:
            return generated_models[schema_name]
        # Try case-insensitive match
        for name, model in generated_models.items():
            if name.lower() == schema_name.lower():
                return model

    # Fall back to simple builder
    return schema_to_model(schema_name, body_schema, _model_cache=model_cache)


# ============================================================
# Fallback: simple model builder (used when datamodel-code-generator
# is not available or for inline schemas not in components/schemas)
# ============================================================

def schema_to_model(
    name: str,
    schema: dict,
    doc: str = "",
    _model_cache: dict[str, type[BaseModel]] | None = None,
) -> type[BaseModel]:
    """Convert a JSON Schema object to a dynamic Pydantic model.

    Simple fallback builder. Handles: primitives, nested objects, arrays,
    enums, dicts, nullable. For full schema support (allOf, oneOf, etc.),
    use generate_models_from_spec() instead.
    """
    if _model_cache is None:
        _model_cache = {}

    if name in _model_cache:
        return _model_cache[name]

    fields: dict[str, Any] = {}
    required_fields = set(schema.get("required", []))
    properties = schema.get("properties", {})

    for field_name, prop in properties.items():
        py_type, field_info = _property_to_field(
            field_name, prop, field_name in required_fields, name, _model_cache
        )
        snake_name = to_snake_case(field_name)
        if snake_name != field_name:
            field_info = FieldInfo(
                default=field_info.default,
                description=field_info.description,
                serialization_alias=field_name,
            )
        fields[snake_name] = (py_type, field_info)

    model = create_model(name, __doc__=doc or name, **fields)
    _model_cache[name] = model
    return model


def _property_to_field(
    field_name: str,
    prop: dict,
    is_required: bool,
    parent_name: str,
    model_cache: dict[str, type[BaseModel]],
) -> tuple[type, FieldInfo]:
    """Convert a single JSON Schema property to a (type, FieldInfo) tuple."""
    prop_type = prop.get("type", "string")

    nullable = False
    if isinstance(prop_type, list):
        non_null = [t for t in prop_type if t != "null"]
        nullable = len(non_null) < len(prop_type)
        prop_type = non_null[0] if non_null else "string"

    if prop_type == "object" and "properties" in prop:
        nested_name = f"{parent_name}_{field_name.title()}"
        nested_model = schema_to_model(nested_name, prop, _model_cache=model_cache)
        py_type = nested_model | None
        return py_type, FieldInfo(default=None)

    if prop_type == "object" and "additionalProperties" in prop:
        additional = prop.get("additionalProperties", {})
        if isinstance(additional, bool):
            py_type = dict[str, Any] | None
        else:
            value_type = TYPE_MAP.get(additional.get("type", "string"), str)
            py_type = dict[str, value_type] | None
        return py_type, FieldInfo(default=None)

    if prop_type == "array":
        items = prop.get("items", {})
        item_type_str = items.get("type", "string")
        if item_type_str == "object" and "properties" in items:
            item_model = schema_to_model(
                f"{parent_name}_{field_name.title()}Item", items, _model_cache=model_cache
            )
            py_type = list[item_model]
        else:
            item_type = TYPE_MAP.get(item_type_str, str)
            py_type = list[item_type]

        if not is_required:
            py_type = py_type | None
            return py_type, FieldInfo(default=None)
        return py_type, FieldInfo()

    enum_values = prop.get("enum")
    if enum_values:
        from enum import Enum
        enum_cls = Enum(f"{parent_name}_{field_name.title()}", {v: v for v in enum_values}, type=str)
        py_type = enum_cls
    else:
        py_type = TYPE_MAP.get(prop_type, str)

    if nullable or not is_required:
        py_type = py_type | None

    default = prop.get("default")
    if default is not None:
        return py_type, FieldInfo(default=default)
    elif is_required and not nullable:
        return py_type, FieldInfo()
    else:
        return py_type, FieldInfo(default=None)
