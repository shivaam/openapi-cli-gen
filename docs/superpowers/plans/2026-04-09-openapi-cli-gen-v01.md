# openapi-cli-gen v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working `openapi-cli-gen` that reads an OpenAPI spec and produces a CLI where nested request bodies become flat `--flags`.

**Architecture:** Manual dispatch layer (parses group + command) delegates to `pydantic-settings CliApp.run()` for flag parsing. Spec loaded via `jsonref` + `openapi-pydantic`. Models generated via `datamodel-code-generator`. Output formatted via `rich`.

**Tech Stack:** Python 3.10+, pydantic-settings, jsonref, openapi-pydantic, httpx, rich, pyyaml, datamodel-code-generator, Jinja2, ruff

**Test runner:** `.venv/bin/python -m pytest` (uv-managed venv at project root)

**Test spec:** `experiments/server/spec.yaml` (15 endpoints, 6 tags — covers all edge cases)

**Test server:** `experiments/server/app.py` (FastAPI, run with `.venv/bin/uvicorn experiments.server.app:app`)

---

## File Map

```
src/openapi_cli_gen/
  __init__.py              # Public API: build_cli(), build_command_group()
  spec/
    __init__.py
    loader.py              # load_spec(path_or_url) → resolved dict
    parser.py              # parse_spec(resolved) → list[EndpointInfo]
  engine/
    __init__.py
    models.py              # schema_to_model(schema) → dynamic Pydantic model
    registry.py            # build_registry(endpoints) → {group: {cmd: (model, endpoint)}}
    dispatch.py            # dispatch(registry, args) — group+cmd routing + CliApp.run
    auth.py                # AuthConfig builder from securitySchemes
  output/
    __init__.py
    formatter.py           # format_output(data, fmt) — JSON/table/YAML/raw
  codegen/
    __init__.py
    generator.py           # generate_package(spec, name, output_dir)
    templates/
      cli.py.jinja2
      pyproject.toml.jinja2
      __init__.py.jinja2
  cli.py                   # Our own CLI: generate/run/inspect commands

tests/
  __init__.py
  conftest.py              # Shared fixtures (spec path, resolved spec, parsed endpoints)
  test_loader.py
  test_parser.py
  test_models.py
  test_registry.py
  test_dispatch.py
  test_auth.py
  test_formatter.py
  test_codegen.py
  test_cli.py              # Integration tests for generate/run/inspect
```

---

### Task 1: Project Setup + Test Infrastructure

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `src/openapi_cli_gen/spec/__init__.py`
- Create: `src/openapi_cli_gen/engine/__init__.py`
- Create: `src/openapi_cli_gen/output/__init__.py`
- Create: `src/openapi_cli_gen/codegen/__init__.py`
- Create: `src/openapi_cli_gen/codegen/templates/` (directory)

- [ ] **Step 1: Add test dependencies to pyproject.toml**

Add `pytest` to dev deps and add a `[project.scripts]` entry:

```toml
[project.scripts]
openapi-cli-gen = "openapi_cli_gen.cli:main"

[project.optional-dependencies]
dev = [
    "datamodel-code-generator>=0.56",
    "ruff>=0.4",
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "typer>=0.12",
    "pydanclick>=0.5",
    "pytest>=8.0",
    "jinja2>=3.1",
]
```

Also add `jinja2` to the main `dependencies` list:

```toml
dependencies = [
    "pydantic-settings>=2.13",
    "jsonref>=1.1",
    "openapi-pydantic>=0.5",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "rich>=13.0",
    "jinja2>=3.1",
]
```

- [ ] **Step 2: Create package structure**

Create empty `__init__.py` files:

```
src/openapi_cli_gen/spec/__init__.py       (empty)
src/openapi_cli_gen/engine/__init__.py     (empty)
src/openapi_cli_gen/output/__init__.py     (empty)
src/openapi_cli_gen/codegen/__init__.py    (empty)
tests/__init__.py                          (empty)
```

- [ ] **Step 3: Create test conftest with shared fixtures**

```python
# tests/conftest.py
from pathlib import Path
import pytest
import yaml
import jsonref

SPEC_PATH = Path(__file__).parent.parent / "experiments" / "server" / "spec.yaml"


@pytest.fixture
def spec_path():
    return SPEC_PATH


@pytest.fixture
def raw_spec():
    return yaml.safe_load(SPEC_PATH.read_text())


@pytest.fixture
def resolved_spec(raw_spec):
    return jsonref.replace_refs(raw_spec)
```

- [ ] **Step 4: Install deps and verify pytest works**

Run: `.venv/bin/uv pip install -e ".[dev]" && .venv/bin/python -m pytest tests/ -v`

Expected: `no tests ran` (0 collected, no errors)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: project setup with test infrastructure and package skeleton"
```

---

### Task 2: Spec Loader

**Files:**
- Create: `src/openapi_cli_gen/spec/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_loader.py
from pathlib import Path
from openapi_cli_gen.spec.loader import load_spec


def test_load_yaml_file(spec_path):
    result = load_spec(str(spec_path))
    assert result["openapi"] == "3.1.0"
    assert "paths" in result
    assert "/users" in result["paths"]


def test_load_resolves_refs(spec_path):
    result = load_spec(str(spec_path))
    # UserCreate schema should have address resolved (not a $ref)
    user_create = result["components"]["schemas"]["UserCreate"]
    address = user_create["properties"]["address"]
    assert "properties" in address  # resolved, not {"$ref": "..."}
    assert "city" in address["properties"]


def test_load_json_file(tmp_path):
    import json
    spec = {"openapi": "3.1.0", "info": {"title": "T", "version": "1"}, "paths": {}}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    result = load_spec(str(p))
    assert result["openapi"] == "3.1.0"


def test_load_nonexistent_file():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_spec("/nonexistent/spec.yaml")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_loader.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'openapi_cli_gen.spec.loader'`

- [ ] **Step 3: Implement loader**

```python
# src/openapi_cli_gen/spec/loader.py
from __future__ import annotations

import json
from pathlib import Path

import jsonref
import yaml


def load_spec(spec_path: str) -> dict:
    """Load an OpenAPI spec from a file path, resolve all $ref references.

    Args:
        spec_path: Path to YAML or JSON OpenAPI spec file.

    Returns:
        Fully resolved spec as a dict (all $ref inlined).

    Raises:
        FileNotFoundError: If spec file does not exist.
    """
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    text = path.read_text()

    if path.suffix in (".json",):
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)

    base_uri = path.absolute().as_uri()
    return jsonref.replace_refs(raw, base_uri=base_uri)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_loader.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/spec/loader.py tests/test_loader.py
git commit -m "feat: spec loader with jsonref resolution"
```

---

### Task 3: Spec Parser

**Files:**
- Create: `src/openapi_cli_gen/spec/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_parser.py
from openapi_cli_gen.spec.parser import parse_spec, EndpointInfo


def test_parse_returns_endpoints(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    assert len(endpoints) > 0
    assert all(isinstance(ep, EndpointInfo) for ep in endpoints)


def test_parse_groups_by_tag(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    tags = {ep.tag for ep in endpoints}
    assert "users" in tags
    assert "orders" in tags
    assert "tags" in tags


def test_parse_extracts_operation_id(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    op_ids = {ep.operation_id for ep in endpoints}
    assert "list_users" in op_ids
    assert "create_user" in op_ids
    assert "get_user" in op_ids


def test_parse_extracts_method_and_path(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.method == "post"
    assert create_user.path == "/users"


def test_parse_classifies_params(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    get_user = next(ep for ep in endpoints if ep.operation_id == "get_user")
    assert "user_id" in [p.name for p in get_user.path_params]

    list_users = next(ep for ep in endpoints if ep.operation_id == "list_users")
    query_names = [p.name for p in list_users.query_params]
    assert "limit" in query_names
    assert "offset" in query_names


def test_parse_extracts_body_schema(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.body_schema is not None
    assert "name" in create_user.body_schema.get("properties", {})


def test_parse_no_body_for_get(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    list_users = next(ep for ep in endpoints if ep.operation_id == "list_users")
    assert list_users.body_schema is None


def test_parse_extracts_summary(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.summary == "Create a new user"


def test_parse_extracts_security_schemes(resolved_spec):
    from openapi_cli_gen.spec.parser import extract_security_schemes, SecuritySchemeInfo
    schemes = extract_security_schemes(resolved_spec)
    assert len(schemes) > 0
    names = {s.name for s in schemes}
    assert "bearerAuth" in names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_parser.py -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement parser**

```python
# src/openapi_cli_gen/spec/parser.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParamInfo:
    name: str
    type: str  # "string", "integer", "number", "boolean"
    required: bool = False
    default: object = None
    enum: list[str] | None = None


@dataclass
class SecuritySchemeInfo:
    name: str
    type: str  # "http", "apiKey", "oauth2", "openIdConnect"
    scheme: str | None = None  # "bearer", "basic" (for http type)
    header_name: str | None = None  # for apiKey type
    location: str | None = None  # "header", "query", "cookie" (for apiKey)


@dataclass
class EndpointInfo:
    operation_id: str
    tag: str
    method: str  # "get", "post", "put", "patch", "delete"
    path: str
    summary: str = ""
    path_params: list[ParamInfo] = field(default_factory=list)
    query_params: list[ParamInfo] = field(default_factory=list)
    body_schema: dict | None = None


HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def parse_spec(resolved_spec: dict) -> list[EndpointInfo]:
    """Parse a resolved OpenAPI spec into a list of EndpointInfo."""
    endpoints = []

    for path, path_item in resolved_spec.get("paths", {}).items():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue

            tag = (operation.get("tags") or ["default"])[0]
            op_id = operation.get("operationId", f"{method}_{path.strip('/').replace('/', '_')}")

            path_params = []
            query_params = []
            for p in operation.get("parameters", []):
                schema = p.get("schema", {})
                param = ParamInfo(
                    name=p["name"],
                    type=schema.get("type", "string"),
                    required=p.get("required", False),
                    default=schema.get("default"),
                    enum=schema.get("enum"),
                )
                if p["in"] == "path":
                    path_params.append(param)
                elif p["in"] == "query":
                    query_params.append(param)

            body_schema = None
            rb = operation.get("requestBody")
            if rb:
                content = rb.get("content", {})
                json_content = content.get("application/json", {})
                body_schema = json_content.get("schema")

            endpoints.append(EndpointInfo(
                operation_id=op_id,
                tag=tag,
                method=method,
                path=path,
                summary=operation.get("summary", ""),
                path_params=path_params,
                query_params=query_params,
                body_schema=body_schema,
            ))

    return endpoints


def extract_security_schemes(resolved_spec: dict) -> list[SecuritySchemeInfo]:
    """Extract security scheme info from spec."""
    schemes = []
    components = resolved_spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    for name, scheme in security_schemes.items():
        schemes.append(SecuritySchemeInfo(
            name=name,
            type=scheme.get("type", ""),
            scheme=scheme.get("scheme"),
            header_name=scheme.get("name"),
            location=scheme.get("in"),
        ))

    return schemes
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_parser.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/spec/parser.py tests/test_parser.py
git commit -m "feat: spec parser extracts endpoints, params, bodies, security schemes"
```

---

### Task 4: Dynamic Model Builder

**Files:**
- Create: `src/openapi_cli_gen/engine/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
from pydantic import BaseModel
from pydantic_settings import CliApp
from openapi_cli_gen.engine.models import schema_to_model


def test_flat_model():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 25},
        },
    }
    Model = schema_to_model("TestFlat", schema)
    assert issubclass(Model, BaseModel)
    instance = Model(name="John")
    assert instance.name == "John"
    assert instance.age == 25


def test_nested_model():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                },
            },
        },
    }
    Model = schema_to_model("TestNested", schema)
    instance = Model(name="John", address={"city": "NYC"})
    assert instance.address.city == "NYC"


def test_array_of_primitives():
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    Model = schema_to_model("TestArray", schema)
    instance = Model(tags=["a", "b"])
    assert instance.tags == ["a", "b"]


def test_nullable_field():
    schema = {
        "type": "object",
        "properties": {
            "value": {"type": ["string", "null"]},
        },
    }
    Model = schema_to_model("TestNullable", schema)
    instance = Model(value=None)
    assert instance.value is None


def test_enum_field():
    schema = {
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["admin", "user"], "default": "user"},
        },
    }
    Model = schema_to_model("TestEnum", schema)
    instance = Model()
    assert instance.role == "user"


def test_dict_field():
    schema = {
        "type": "object",
        "properties": {
            "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
        },
    }
    Model = schema_to_model("TestDict", schema)
    instance = Model(metadata={"k": "v"})
    assert instance.metadata == {"k": "v"}


def test_model_works_with_cliapp():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 25},
        },
    }
    Model = schema_to_model("TestCli", schema)
    Model.cli_cmd = lambda self: None
    CliApp.run(Model, cli_args=["--name", "John", "--age", "30"])


def test_nested_model_works_with_cliapp():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
            },
        },
    }
    Model = schema_to_model("TestNestedCli", schema)
    Model.cli_cmd = lambda self: None
    CliApp.run(Model, cli_args=["--name", "John", "--address.city", "NYC"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_models.py -v`

Expected: FAIL

- [ ] **Step 3: Implement model builder**

```python
# src/openapi_cli_gen/engine/models.py
from __future__ import annotations

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
        fields[field_name] = (py_type, field_info)

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
        value_type = TYPE_MAP.get(
            prop.get("additionalProperties", {}).get("type", "string"), str
        )
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
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_models.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/engine/models.py tests/test_models.py
git commit -m "feat: dynamic Pydantic model builder from JSON Schema"
```

---

### Task 5: Command Registry

**Files:**
- Create: `src/openapi_cli_gen/engine/registry.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_registry.py
from pydantic import BaseModel
from openapi_cli_gen.spec.loader import load_spec
from openapi_cli_gen.spec.parser import parse_spec
from openapi_cli_gen.engine.registry import build_registry, CommandInfo


def test_build_registry(spec_path):
    resolved = load_spec(str(spec_path))
    endpoints = parse_spec(resolved)
    registry = build_registry(endpoints)

    assert "users" in registry
    assert "orders" in registry
    assert "tags" in registry


def test_registry_has_commands(spec_path):
    resolved = load_spec(str(spec_path))
    endpoints = parse_spec(resolved)
    registry = build_registry(endpoints)

    user_cmds = set(registry["users"].keys())
    assert "list" in user_cmds or "list-users" in user_cmds
    assert "create" in user_cmds or "create-user" in user_cmds


def test_registry_commands_have_models(spec_path):
    resolved = load_spec(str(spec_path))
    endpoints = parse_spec(resolved)
    registry = build_registry(endpoints)

    for group, commands in registry.items():
        for cmd_name, cmd_info in commands.items():
            assert isinstance(cmd_info, CommandInfo)
            assert issubclass(cmd_info.model, BaseModel)
            assert cmd_info.endpoint is not None


def test_command_model_has_correct_fields(spec_path):
    resolved = load_spec(str(spec_path))
    endpoints = parse_spec(resolved)
    registry = build_registry(endpoints)

    # Find the create user command
    users = registry["users"]
    create_cmd = None
    for name, info in users.items():
        if "create" in name:
            create_cmd = info
            break

    assert create_cmd is not None
    fields = create_cmd.model.model_fields
    assert "name" in fields
    assert "email" in fields
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_registry.py -v`

Expected: FAIL

- [ ] **Step 3: Implement registry builder**

```python
# src/openapi_cli_gen/engine/registry.py
from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel

from openapi_cli_gen.engine.models import schema_to_model, TYPE_MAP
from openapi_cli_gen.spec.parser import EndpointInfo, ParamInfo
from pydantic.fields import FieldInfo


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

    Strategy: strip the tag prefix from operationId, kebab-case the rest.
    Examples: list_users → list, create_user → create, get_user → get
    """
    op_id = ep.operation_id
    tag = ep.tag

    # Try stripping tag prefix (singular or plural)
    singular = tag.rstrip("s") if tag.endswith("s") else tag
    for prefix in [f"{tag}_", f"{singular}_"]:
        if op_id.startswith(prefix):
            remainder = op_id[len(prefix):]
            if remainder:
                return _to_kebab(remainder)

    # Try stripping verb prefix and check if tag is the suffix
    for verb in ("list", "get", "create", "update", "delete", "patch", "send", "trigger"):
        if op_id.startswith(f"{verb}_"):
            return verb

    return _to_kebab(op_id)


def _to_kebab(name: str) -> str:
    """Convert snake_case or camelCase to kebab-case."""
    # snake_case → kebab-case
    name = name.replace("_", "-")
    # camelCase → kebab-case
    name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name).lower()
    return name


def _build_command_model(
    ep: EndpointInfo,
    model_cache: dict[str, type[BaseModel]],
) -> type[BaseModel]:
    """Build a dynamic Pydantic model for a command, combining params + body."""
    from pydantic import create_model

    fields: dict[str, tuple] = {}

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
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_registry.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/engine/registry.py tests/test_registry.py
git commit -m "feat: command registry builder from parsed endpoints"
```

---

### Task 6: Output Formatter

**Files:**
- Create: `src/openapi_cli_gen/output/formatter.py`
- Create: `tests/test_formatter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_formatter.py
from openapi_cli_gen.output.formatter import format_output


def test_format_json():
    data = {"name": "John", "age": 30}
    result = format_output(data, "json")
    assert '"name": "John"' in result
    assert '"age": 30' in result


def test_format_yaml():
    data = {"name": "John", "age": 30}
    result = format_output(data, "yaml")
    assert "name: John" in result
    assert "age: 30" in result


def test_format_raw():
    data = {"name": "John"}
    result = format_output(data, "raw")
    assert "name" in result


def test_format_table_single(capsys):
    data = {"name": "John", "age": 30}
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "name" in captured.out.lower() or "John" in captured.out


def test_format_table_list(capsys):
    data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "A" in captured.out
    assert "B" in captured.out


def test_format_table_wrapped_list(capsys):
    data = {"items": [{"id": 1}, {"id": 2}], "total": 2}
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "total" in captured.out.lower() or "2" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_formatter.py -v`

Expected: FAIL

- [ ] **Step 3: Implement formatter**

```python
# src/openapi_cli_gen/output/formatter.py
from __future__ import annotations

import json
import sys

import yaml
from rich.console import Console
from rich.table import Table


def format_output(
    data: dict | list,
    fmt: str = "json",
    print_output: bool = False,
) -> str | None:
    """Format API response data for CLI output.

    Args:
        data: The response data to format.
        fmt: One of "json", "yaml", "table", "raw".
        print_output: If True, print directly (required for table). Otherwise return string.

    Returns:
        Formatted string for json/yaml/raw, or None for table (printed directly).
    """
    if fmt == "json":
        result = json.dumps(data, indent=2, default=str)
    elif fmt == "yaml":
        result = yaml.dump(data, default_flow_style=False, sort_keys=False)
    elif fmt == "raw":
        result = str(data)
    elif fmt == "table":
        _print_table(data)
        return None
    else:
        result = json.dumps(data, indent=2, default=str)

    if print_output:
        print(result)
    return result


def _print_table(data: dict | list) -> None:
    """Print data as a rich table."""
    console = Console()

    rows = None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        for key in ("items", "results", "data"):
            if key in data and isinstance(data[key], list):
                rows = data[key]
                for k, v in data.items():
                    if k != key:
                        console.print(f"[dim]{k}:[/dim] {v}")
                break

    if rows and len(rows) > 0:
        table = Table(show_header=True, header_style="bold")
        keys = list(rows[0].keys())
        for key in keys:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row.get(k, "")) for k in keys])
        console.print(table)
    elif isinstance(data, dict):
        table = Table(show_header=True, header_style="bold")
        table.add_column("Field")
        table.add_column("Value")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            table.add_row(str(key), str(value))
        console.print(table)
    else:
        console.print(str(data))
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_formatter.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/output/formatter.py tests/test_formatter.py
git commit -m "feat: output formatter — JSON, YAML, table, raw"
```

---

### Task 7: Auth Config

**Files:**
- Create: `src/openapi_cli_gen/engine/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_auth.py
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
    # Ensure env var is not set
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_auth.py -v`

Expected: FAIL

- [ ] **Step 3: Implement auth**

```python
# src/openapi_cli_gen/engine/auth.py
from __future__ import annotations

from pydantic_settings import BaseSettings
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

    Reads {CLI_NAME}_TOKEN and {CLI_NAME}_API_KEY from environment.
    """
    prefix = cli_name.upper().replace("-", "_")
    state = AuthState()

    for scheme in schemes:
        if scheme.type == "http" and scheme.scheme == "bearer":
            state._scheme_type = "bearer"
            config = _make_settings(prefix, "TOKEN")
            if config.token:
                state._headers = {"Authorization": f"Bearer {config.token}"}
            break
        elif scheme.type == "apiKey" and scheme.location == "header":
            state._scheme_type = "apiKey"
            state._header_name = scheme.header_name or "X-API-Key"
            config = _make_settings(prefix, "API_KEY")
            if config.token:
                state._headers = {state._header_name: config.token}
            break
        elif scheme.type == "http" and scheme.scheme == "basic":
            state._scheme_type = "basic"
            # Basic auth deferred for now
            break

    return state


def _make_settings(prefix: str, suffix: str) -> BaseSettings:
    """Dynamically create a BaseSettings that reads one env var."""
    from pydantic_settings import BaseSettings as BS

    class _AuthSettings(BS):
        model_config = {"env_prefix": f"{prefix}_"}
        token: str | None = None

    # Map TOKEN or API_KEY to the generic 'token' field
    import os
    env_key = f"{prefix}_{suffix}"
    value = os.environ.get(env_key)

    return _AuthSettings(token=value) if value else _AuthSettings()
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_auth.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/engine/auth.py tests/test_auth.py
git commit -m "feat: auth config from security schemes + env vars"
```

---

### Task 8: Dispatch + Builder (build_cli)

**Files:**
- Create: `src/openapi_cli_gen/engine/dispatch.py`
- Create: `src/openapi_cli_gen/engine/builder.py`
- Modify: `src/openapi_cli_gen/__init__.py`
- Create: `tests/test_dispatch.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_dispatch.py
import io
import sys
from openapi_cli_gen import build_cli


def test_build_cli_returns_callable(spec_path):
    app = build_cli(spec=str(spec_path), name="testcli")
    assert callable(app)


def test_dispatch_help(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "users" in captured.out
    assert "orders" in captured.out


def test_dispatch_group_help(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["users", "--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "list" in captured.out or "create" in captured.out


def test_dispatch_unknown_group(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["nonexistent"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "unknown" in captured.out.lower() or "error" in captured.out.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_dispatch.py -v`

Expected: FAIL

- [ ] **Step 3: Implement dispatch**

```python
# src/openapi_cli_gen/engine/dispatch.py
from __future__ import annotations

import sys

from pydantic_settings import CliApp

from openapi_cli_gen.engine.registry import CommandInfo


def dispatch(
    registry: dict[str, dict[str, CommandInfo]],
    args: list[str],
    name: str = "cli",
) -> None:
    """Dispatch CLI args to the right command via manual group+command routing."""
    if not args or args[0] in ("-h", "--help"):
        _print_root_help(registry, name)
        return

    group = args[0]
    if group not in registry:
        print(f"Error: unknown group '{group}'. Available: {', '.join(registry.keys())}")
        sys.exit(1)

    remaining = args[1:]
    if not remaining or remaining[0] in ("-h", "--help"):
        _print_group_help(registry[group], group, name)
        return

    command = remaining[0]
    if command not in registry[group]:
        print(f"Error: unknown command '{group} {command}'. Available: {', '.join(registry[group].keys())}")
        sys.exit(1)

    cmd_info = registry[group][command]
    flag_args = remaining[1:]

    CliApp.run(cmd_info.model, cli_args=flag_args)


def _print_root_help(
    registry: dict[str, dict[str, CommandInfo]],
    name: str,
) -> None:
    print(f"Usage: {name} <group> <command> [options]\n")
    print("Groups:")
    for group, commands in sorted(registry.items()):
        cmds = ", ".join(sorted(commands.keys()))
        print(f"  {group:20} {cmds}")
    print(f"\nUse '{name} <group> --help' for group help")


def _print_group_help(
    commands: dict[str, CommandInfo],
    group: str,
    name: str,
) -> None:
    print(f"Usage: {name} {group} <command> [options]\n")
    print("Commands:")
    for cmd_name, cmd_info in sorted(commands.items()):
        doc = cmd_info.endpoint.summary or cmd_info.endpoint.operation_id
        print(f"  {cmd_name:20} {doc}")
```

- [ ] **Step 4: Implement builder**

```python
# src/openapi_cli_gen/engine/builder.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import httpx

from openapi_cli_gen.spec.loader import load_spec
from openapi_cli_gen.spec.parser import parse_spec, extract_security_schemes
from openapi_cli_gen.engine.registry import build_registry
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
        spec: Path to OpenAPI spec file.
        name: CLI name (used for help text and env var prefix).
        base_url: Override the API base URL. If None, uses first server from spec.

    Returns:
        A callable that accepts a list of args (or uses sys.argv[1:]).
    """
    spec_path = str(spec)
    resolved = load_spec(spec_path)
    endpoints = parse_spec(resolved)
    security_schemes = extract_security_schemes(resolved)
    registry = build_registry(endpoints)
    auth_state = build_auth_config(name, security_schemes)

    # Determine base URL
    if base_url is None:
        servers = resolved.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost:8000"

    # Attach cli_cmd to each model
    for group_cmds in registry.values():
        for cmd_info in group_cmds.values():
            _attach_cli_cmd(cmd_info, base_url, auth_state)

    def app(args: list[str] | None = None):
        if args is None:
            args = sys.argv[1:]
        dispatch(registry, args, name=name)

    return app


def _attach_cli_cmd(cmd_info, base_url: str, auth_state) -> None:
    """Attach a cli_cmd method to the command model that makes the HTTP call."""
    ep = cmd_info.endpoint

    def cli_cmd(self):
        data = self.model_dump(exclude_none=True)

        # Separate path params from body/query
        path_names = {p.name for p in ep.path_params}
        query_names = {p.name for p in ep.query_params}

        path_params = {k: v for k, v in data.items() if k in path_names}
        query_params = {k: v for k, v in data.items() if k in query_names}
        body = {k: v for k, v in data.items() if k not in path_names and k not in query_names}

        # Build URL with path params
        path = ep.path
        for k, v in path_params.items():
            path = path.replace(f"{{{k}}}", str(v))
        url = f"{base_url}{path}"

        # Determine output format
        output_fmt = body.pop("output_format", "json") if "output_format" in body else "json"

        headers = auth_state.get_headers()

        with httpx.Client() as client:
            if ep.method in ("post", "put", "patch"):
                resp = client.request(ep.method.upper(), url, json=body or None, params=query_params, headers=headers)
            else:
                resp = client.request(ep.method.upper(), url, params=query_params, headers=headers)

        if resp.status_code >= 400:
            print(f"Error: {resp.status_code}")
            try:
                print(format_output(resp.json(), "json"))
            except Exception:
                print(resp.text)
            raise SystemExit(1)

        try:
            result = resp.json()
        except Exception:
            result = resp.text

        output = format_output(result, output_fmt)
        if output is not None:
            print(output)

    cmd_info.model.cli_cmd = cli_cmd
```

- [ ] **Step 5: Update `__init__.py` with public API**

```python
# src/openapi_cli_gen/__init__.py
"""Generate typed Python CLIs from OpenAPI specs with Pydantic model flattening."""

__version__ = "0.0.1"

from openapi_cli_gen.engine.builder import build_cli

__all__ = ["build_cli", "__version__"]
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/python -m pytest tests/test_dispatch.py -v`

Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add src/openapi_cli_gen/ tests/test_dispatch.py
git commit -m "feat: dispatch + builder — build_cli() public API working"
```

---

### Task 9: Code Generation (generate command)

**Files:**
- Create: `src/openapi_cli_gen/codegen/generator.py`
- Create: `src/openapi_cli_gen/codegen/templates/cli.py.jinja2`
- Create: `src/openapi_cli_gen/codegen/templates/pyproject.toml.jinja2`
- Create: `src/openapi_cli_gen/codegen/templates/__init__.py.jinja2`
- Create: `tests/test_codegen.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_codegen.py
from pathlib import Path
from openapi_cli_gen.codegen.generator import generate_package


def test_generate_creates_directory(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    assert output.exists()
    assert (output / "pyproject.toml").exists()


def test_generate_creates_cli_py(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    cli_py = output / "src" / "mycli" / "cli.py"
    assert cli_py.exists()
    content = cli_py.read_text()
    assert "build_cli" in content
    assert "mycli" in content


def test_generate_copies_spec(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    spec = output / "src" / "mycli" / "spec.yaml"
    assert spec.exists()


def test_generate_creates_pyproject(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    pyproject = output / "pyproject.toml"
    content = pyproject.read_text()
    assert "mycli" in content
    assert "openapi-cli-gen" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_codegen.py -v`

Expected: FAIL

- [ ] **Step 3: Create Jinja2 templates**

```jinja2
{# src/openapi_cli_gen/codegen/templates/cli.py.jinja2 #}
from pathlib import Path
from openapi_cli_gen import build_cli

app = build_cli(
    spec=Path(__file__).parent / "spec.yaml",
    name="{{ name }}",
)


def main():
    app()


if __name__ == "__main__":
    main()
```

```jinja2
{# src/openapi_cli_gen/codegen/templates/pyproject.toml.jinja2 #}
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{ name }}"
version = "0.1.0"
description = "CLI for {{ name }} API"
requires-python = ">=3.10"
dependencies = [
    "openapi-cli-gen>={{ openapi_cli_gen_version }}",
]

[project.scripts]
{{ name }} = "{{ name }}.cli:main"
```

```jinja2
{# src/openapi_cli_gen/codegen/templates/__init__.py.jinja2 #}
"""{{ name }} CLI — generated by openapi-cli-gen."""
```

- [ ] **Step 4: Implement generator**

```python
# src/openapi_cli_gen/codegen/generator.py
from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader

import openapi_cli_gen


def generate_package(
    spec: str,
    name: str,
    output_dir: str,
) -> Path:
    """Generate a CLI package from an OpenAPI spec.

    Args:
        spec: Path to OpenAPI spec file.
        name: Package/CLI name.
        output_dir: Directory to write the generated package.

    Returns:
        Path to the generated package directory.
    """
    output = Path(output_dir)
    pkg_dir = output / "src" / name

    # Create directory structure
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Load templates
    env = Environment(
        loader=PackageLoader("openapi_cli_gen", "codegen/templates"),
        keep_trailing_newline=True,
    )

    context = {
        "name": name,
        "openapi_cli_gen_version": openapi_cli_gen.__version__,
    }

    # Render templates
    for template_name, output_path in [
        ("cli.py.jinja2", pkg_dir / "cli.py"),
        ("__init__.py.jinja2", pkg_dir / "__init__.py"),
        ("pyproject.toml.jinja2", output / "pyproject.toml"),
    ]:
        template = env.get_template(template_name)
        output_path.write_text(template.render(**context))

    # Copy spec file
    shutil.copy2(spec, pkg_dir / "spec.yaml")

    return output
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/test_codegen.py -v`

Expected: all passed

- [ ] **Step 6: Commit**

```bash
git add src/openapi_cli_gen/codegen/ tests/test_codegen.py
git commit -m "feat: code generation — generate CLI package from spec"
```

---

### Task 10: Our CLI (generate/run/inspect commands)

**Files:**
- Create: `src/openapi_cli_gen/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
import subprocess
import sys
from pathlib import Path


def _run_cli(*args):
    """Run our CLI as a subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "openapi_cli_gen", *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    return result


def test_cli_help():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "generate" in result.stdout
    assert "run" in result.stdout
    assert "inspect" in result.stdout


def test_inspect_command(spec_path):
    result = _run_cli("inspect", "--spec", str(spec_path))
    assert result.returncode == 0
    assert "endpoints" in result.stdout.lower() or "groups" in result.stdout.lower()


def test_generate_command(spec_path, tmp_path):
    output = tmp_path / "testcli"
    result = _run_cli("generate", "--spec", str(spec_path), "--name", "testcli", "--output", str(output))
    assert result.returncode == 0
    assert (output / "pyproject.toml").exists()
    assert (output / "src" / "testcli" / "cli.py").exists()
    assert (output / "src" / "testcli" / "spec.yaml").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`

Expected: FAIL

- [ ] **Step 3: Implement CLI**

```python
# src/openapi_cli_gen/cli.py
from __future__ import annotations

import sys
from pathlib import Path

import typer

from openapi_cli_gen.spec.loader import load_spec
from openapi_cli_gen.spec.parser import parse_spec, extract_security_schemes

app = typer.Typer(
    name="openapi-cli-gen",
    help="Generate typed Python CLIs from OpenAPI specs.",
)


@app.command()
def generate(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
    name: str = typer.Option(..., help="CLI/package name"),
    output: str = typer.Option(None, help="Output directory (default: ./<name>)"),
):
    """Generate a CLI package from an OpenAPI spec."""
    from openapi_cli_gen.codegen.generator import generate_package

    output_dir = output or f"./{name}"
    result = generate_package(spec=spec, name=name, output_dir=output_dir)
    typer.echo(f"Generated CLI package at: {result}")


@app.command()
def run(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
    args: list[str] = typer.Argument(None, help="Command args: <group> <command> [--flags]"),
):
    """Run a CLI directly from an OpenAPI spec (no code generation)."""
    from openapi_cli_gen import build_cli

    cli = build_cli(spec=spec, name="cli")
    cli(args or [])


@app.command()
def inspect(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
):
    """Inspect an OpenAPI spec — show what would be generated."""
    resolved = load_spec(spec)
    endpoints = parse_spec(resolved)
    schemes = extract_security_schemes(resolved)

    # Group by tag
    groups: dict[str, list] = {}
    for ep in endpoints:
        groups.setdefault(ep.tag, []).append(ep)

    title = resolved.get("info", {}).get("title", "Unknown")
    version = resolved.get("info", {}).get("version", "?")

    typer.echo(f"API: {title} v{version}")
    typer.echo(f"Endpoints: {len(endpoints)}")
    typer.echo(f"Groups: {len(groups)}")
    typer.echo(f"Auth schemes: {len(schemes)}")
    typer.echo()

    for group_name, eps in sorted(groups.items()):
        typer.echo(f"  {group_name}:")
        for ep in eps:
            body = " [body]" if ep.body_schema else ""
            typer.echo(f"    {ep.method.upper():7} {ep.path:30} {ep.summary}{body}")


def main():
    app()


if __name__ == "__main__":
    main()
```

Also create `src/openapi_cli_gen/__main__.py`:

```python
# src/openapi_cli_gen/__main__.py
from openapi_cli_gen.cli import main

main()
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/openapi_cli_gen/cli.py src/openapi_cli_gen/__main__.py tests/test_cli.py
git commit -m "feat: CLI commands — generate, run, inspect"
```

---

### Task 11: Integration Test — End to End

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end integration test: spec → build_cli → dispatch → help output."""
from openapi_cli_gen import build_cli


def test_full_pipeline_help(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["--help"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "users" in out
    assert "orders" in out
    assert "tags" in out
    assert "jobs" in out


def test_full_pipeline_command_help(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["users", "create", "--help"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "--name" in out
    assert "--email" in out


def test_full_pipeline_group_help(spec_path, capsys):
    app = build_cli(spec=str(spec_path), name="testcli")
    try:
        app(["users", "--help"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    # Should list available commands
    assert "list" in out or "create" in out or "get" in out


def test_generate_and_inspect(spec_path, tmp_path, capsys):
    """Generate a package, then verify inspect still works on the spec."""
    from openapi_cli_gen.codegen.generator import generate_package

    output = tmp_path / "e2ecli"
    generate_package(spec=str(spec_path), name="e2ecli", output_dir=str(output))

    # Verify generated spec is loadable
    generated_spec = output / "src" / "e2ecli" / "spec.yaml"
    app = build_cli(spec=str(generated_spec), name="e2ecli")
    try:
        app(["--help"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "users" in out
```

- [ ] **Step 2: Run all tests**

Run: `.venv/bin/python -m pytest tests/ -v`

Expected: all passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: integration tests — full pipeline validated"
```

---

### Task 12: Final Polish + README

**Files:**
- Modify: `README.md`
- Modify: `src/openapi_cli_gen/__init__.py` (add `build_command_group`)

- [ ] **Step 1: Add build_command_group to public API**

```python
# src/openapi_cli_gen/__init__.py
"""Generate typed Python CLIs from OpenAPI specs with Pydantic model flattening."""

__version__ = "0.0.1"

from openapi_cli_gen.engine.builder import build_cli, build_command_group

__all__ = ["build_cli", "build_command_group", "__version__"]
```

Add `build_command_group` to `builder.py`:

```python
# Add to src/openapi_cli_gen/engine/builder.py

def build_command_group(
    spec: str | Path,
    name: str = "api",
    base_url: str | None = None,
    subparsers=None,
) -> dict[str, dict[str, CommandInfo]]:
    """Build command group from spec and optionally attach to existing argparse subparsers.

    Returns the registry for programmatic use.
    """
    spec_path = str(spec)
    resolved = load_spec(spec_path)
    endpoints = parse_spec(resolved)
    security_schemes = extract_security_schemes(resolved)
    registry = build_registry(endpoints)
    auth_state = build_auth_config(name, security_schemes)

    if base_url is None:
        servers = resolved.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost:8000"

    for group_cmds in registry.values():
        for cmd_info in group_cmds.values():
            _attach_cli_cmd(cmd_info, base_url, auth_state)

    return registry
```

- [ ] **Step 2: Update README**

Replace README.md with a working quickstart showing all three modes (generate, run, inspect) with real examples against the test spec.

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`

Expected: all passed

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: v0.1 complete — build_cli, build_command_group, generate, run, inspect"
```

- [ ] **Step 5: Push**

```bash
git push origin main
```
