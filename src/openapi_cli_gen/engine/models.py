from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def to_snake_case(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def schema_to_model(
    name: str,
    schema: dict,
    doc: str = "",
    _model_cache: dict[str, type[BaseModel]] | None = None,
) -> type[BaseModel]:
    """Convert a JSON Schema object to a dynamic Pydantic model.

    Handles: primitives, nested objects, arrays, enums, dicts, nullable.
    Nested objects become nested BaseModel subclasses (works with CliApp dot-notation).
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

    # Handle nullable (3.1 style: type as list)
    nullable = False
    if isinstance(prop_type, list):
        non_null = [t for t in prop_type if t != "null"]
        nullable = len(non_null) < len(prop_type)
        prop_type = non_null[0] if non_null else "string"

    # Handle nested object with properties → nested BaseModel
    if prop_type == "object" and "properties" in prop:
        nested_name = f"{parent_name}_{field_name.title()}"
        nested_model = schema_to_model(nested_name, prop, _model_cache=model_cache)
        py_type = nested_model | None
        return py_type, FieldInfo(default=None)

    # Handle dict (additionalProperties without properties)
    if prop_type == "object" and "additionalProperties" in prop:
        additional = prop.get("additionalProperties", {})
        if isinstance(additional, bool):
            # additionalProperties: true means any dict
            py_type = dict[str, Any] | None
        else:
            value_type = TYPE_MAP.get(additional.get("type", "string"), str)
            py_type = dict[str, value_type] | None
        return py_type, FieldInfo(default=None)

    # Handle array
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

    # Handle enum
    enum_values = prop.get("enum")
    if enum_values:
        enum_cls = Enum(f"{parent_name}_{field_name.title()}", {v: v for v in enum_values}, type=str)
        py_type = enum_cls
    else:
        py_type = TYPE_MAP.get(prop_type, str)

    # Handle nullable
    if nullable or not is_required:
        py_type = py_type | None

    default = prop.get("default")
    if default is not None:
        return py_type, FieldInfo(default=default)
    elif is_required and not nullable:
        return py_type, FieldInfo()
    else:
        return py_type, FieldInfo(default=None)
