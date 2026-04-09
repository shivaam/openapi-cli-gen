"""
Experiment 8: End-to-end prototype.

Parse spec → extract endpoints → build CLI → run command → make HTTP call.
This is the MVP in ~150 lines.
"""

import json
import sys
import time
from pathlib import Path

import httpx
import jsonref
import yaml
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_settings import CliApp


# ============================
# Step 1: Parse spec
# ============================

def load_spec(spec_path: str) -> dict:
    """Load and resolve an OpenAPI spec."""
    raw = yaml.safe_load(Path(spec_path).read_text())
    return jsonref.replace_refs(raw)


def extract_endpoints(spec: dict) -> dict[str, list[dict]]:
    """Extract endpoints grouped by tag."""
    groups: dict[str, list[dict]] = {}

    for path, path_item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not operation:
                continue

            tag = (operation.get("tags") or ["default"])[0]
            op_id = operation.get("operationId", f"{method}_{path}")

            # Extract path params
            path_params = []
            query_params = []
            for p in operation.get("parameters", []):
                param = {
                    "name": p["name"],
                    "type": p.get("schema", {}).get("type", "string"),
                    "required": p.get("required", False),
                    "default": p.get("schema", {}).get("default"),
                    "enum": p.get("schema", {}).get("enum"),
                }
                if p["in"] == "path":
                    path_params.append(param)
                elif p["in"] == "query":
                    query_params.append(param)

            # Extract body schema
            body_schema = None
            rb = operation.get("requestBody")
            if rb:
                content = rb.get("content", {})
                json_content = content.get("application/json", {})
                body_schema = json_content.get("schema")

            groups.setdefault(tag, []).append({
                "operation_id": op_id,
                "method": method,
                "path": path,
                "summary": operation.get("summary", ""),
                "path_params": path_params,
                "query_params": query_params,
                "body_schema": body_schema,
            })

    return groups


# ============================
# Step 2: Build Pydantic models from schema
# ============================

TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def schema_to_fields(schema: dict, depth: int = 0) -> dict[str, tuple]:
    """Convert a JSON Schema to Pydantic field definitions.

    Returns dict of {field_name: (type, FieldInfo)} for create_model().
    """
    if not schema or schema.get("type") != "object":
        return {}

    fields = {}
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    for name, prop in properties.items():
        prop_type = prop.get("type", "string")

        # Handle nullable (3.1 style: type as list)
        if isinstance(prop_type, list):
            prop_type = [t for t in prop_type if t != "null"][0] if prop_type else "string"

        # Handle nested object — flatten with dot notation up to depth 2
        if prop_type == "object" and "properties" in prop and depth < 2:
            nested = schema_to_fields(prop, depth + 1)
            for nested_name, nested_def in nested.items():
                fields[f"{name}__{nested_name}"] = nested_def
            continue

        # Handle array
        if prop_type == "array":
            item_type = prop.get("items", {}).get("type", "string")
            if item_type in TYPE_MAP:
                py_type = list[TYPE_MAP[item_type]]
            else:
                py_type = list[str]  # fallback: JSON strings
            default = None
            fields[name] = (py_type | None, FieldInfo(default=default))
            continue

        # Handle enum
        enum_values = prop.get("enum")

        # Map to Python type
        py_type = TYPE_MAP.get(prop_type, str)

        # Default
        default = prop.get("default")
        if name not in required:
            py_type = py_type | None
            if default is None:
                default = None

        if default is not None:
            fields[name] = (py_type, FieldInfo(default=default))
        elif name in required:
            fields[name] = (py_type, FieldInfo())
        else:
            fields[name] = (py_type, FieldInfo(default=None))

    return fields


# ============================
# Step 3: Build CLI with dispatch
# ============================

def build_cli(spec_path: str, base_url: str = "http://localhost:8000"):
    """Build a CLI from an OpenAPI spec."""
    spec = load_spec(spec_path)
    groups = extract_endpoints(spec)

    # Build command registry
    registry: dict[str, dict[str, tuple[type[BaseModel], dict]]] = {}

    for tag, endpoints in groups.items():
        registry[tag] = {}
        for ep in endpoints:
            # Build fields from params + body
            fields = {}

            for p in ep["path_params"]:
                py_type = TYPE_MAP.get(p["type"], str)
                fields[p["name"]] = (py_type, FieldInfo())

            for p in ep["query_params"]:
                py_type = TYPE_MAP.get(p["type"], str)
                default = p.get("default")
                if not p["required"]:
                    py_type = py_type | None
                    default = default if default is not None else None
                if default is not None:
                    fields[p["name"]] = (py_type, FieldInfo(default=default))
                else:
                    fields[p["name"]] = (py_type, FieldInfo(default=None) if not p["required"] else FieldInfo())

            if ep["body_schema"]:
                body_fields = schema_to_fields(ep["body_schema"])
                fields.update(body_fields)

            # Derive command name from operationId
            cmd_name = ep["operation_id"]
            # Remove tag prefix if present (e.g., "list_users" → "list")
            for prefix in [f"{tag}_", f"{tag}s_", f"create_", f"list_", f"get_", f"update_", f"delete_"]:
                if cmd_name.startswith(prefix):
                    cmd_name = cmd_name[len(prefix):] or cmd_name
                    break

            # Simplify: use the HTTP verb as fallback
            verb_map = {"get": "list", "post": "create", "put": "update", "delete": "delete"}
            if not cmd_name or cmd_name == ep["operation_id"]:
                cmd_name = verb_map.get(ep["method"], ep["method"])

            # If path has {id}, it's get/update/delete, not list
            if "{" in ep["path"] and cmd_name == "list":
                cmd_name = "get"

            # Create dynamic Pydantic model
            model_name = f"{tag.title()}{cmd_name.title()}Cmd"
            if fields:
                model = create_model(model_name, __doc__=ep["summary"], **fields)
            else:
                model = create_model(model_name, __doc__=ep["summary"])

            registry[tag][cmd_name] = (model, ep)

    return registry


def dispatch(registry, args: list[str], base_url: str = "http://localhost:8000"):
    """Dispatch CLI args to the right command."""
    if not args or args[0] in ("-h", "--help"):
        print("Usage: mycli <group> <command> [options]\n")
        print("Groups:")
        for tag, commands in registry.items():
            cmds = ", ".join(commands.keys())
            print(f"  {tag:15} {cmds}")
        return

    group = args[0]
    if group not in registry:
        print(f"Error: unknown group '{group}'. Available: {', '.join(registry.keys())}")
        return

    remaining = args[1:]
    if not remaining or remaining[0] in ("-h", "--help"):
        print(f"Usage: mycli {group} <command> [options]\n")
        print("Commands:")
        for cmd_name, (model, ep) in registry[group].items():
            print(f"  {cmd_name:15} {ep['summary']}")
        return

    command = remaining[0]
    if command not in registry[group]:
        print(f"Error: unknown command '{group} {command}'. Available: {', '.join(registry[group].keys())}")
        return

    model, ep = registry[group][command]
    flag_args = remaining[1:]

    # Add cli_cmd to the model dynamically
    def make_cli_cmd(endpoint, url):
        def cli_cmd(self):
            # Reconstruct body from flat fields
            data = self.model_dump(exclude_none=True)

            # Unflatten __ back to nested dicts
            body = {}
            flat = {}
            for key, value in data.items():
                if "__" in key:
                    parts = key.split("__")
                    target = body
                    for part in parts[:-1]:
                        target = target.setdefault(part, {})
                    target[parts[-1]] = value
                else:
                    flat[key] = value

            # Separate path params from body
            path_param_names = {p["name"] for p in endpoint["path_params"]}
            query_param_names = {p["name"] for p in endpoint["query_params"]}

            path_params = {k: v for k, v in flat.items() if k in path_param_names}
            query_params = {k: v for k, v in flat.items() if k in query_param_names}
            body_fields = {k: v for k, v in flat.items() if k not in path_param_names and k not in query_param_names}
            body_fields.update(body)  # merge nested

            # Build URL
            path = endpoint["path"]
            for k, v in path_params.items():
                path = path.replace(f"{{{k}}}", str(v))

            full_url = f"{url}{path}"

            # Make HTTP call
            method = endpoint["method"]
            print(f"\n  → {method.upper()} {full_url}")
            if query_params:
                print(f"    Query: {query_params}")
            if body_fields and method in ("post", "put", "patch"):
                print(f"    Body: {json.dumps(body_fields, indent=2)}")

            try:
                with httpx.Client() as client:
                    if method in ("post", "put", "patch"):
                        resp = client.request(method.upper(), full_url, json=body_fields, params=query_params)
                    else:
                        resp = client.request(method.upper(), full_url, params=query_params)

                    print(f"    Status: {resp.status_code}")
                    if resp.status_code < 300 and resp.text:
                        try:
                            print(f"    Response: {json.dumps(resp.json(), indent=2)}")
                        except Exception:
                            print(f"    Response: {resp.text[:200]}")
            except httpx.ConnectError:
                print("    [Server not running — showing request only]")

        return cli_cmd

    # Monkey-patch cli_cmd onto the model
    model.cli_cmd = make_cli_cmd(ep, base_url)
    CliApp.run(model, cli_args=flag_args)


# ============================
# Test
# ============================

if __name__ == "__main__":
    spec_path = str(Path(__file__).parent.parent / "server" / "spec.yaml")

    print("=" * 60)
    print("EXPERIMENT 8: End-to-End Prototype")
    print("=" * 60)

    print("\n--- Building CLI from spec ---")
    start = time.perf_counter()
    registry = build_cli(spec_path)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Built in {elapsed:.1f}ms")
    print(f"  Groups: {list(registry.keys())}")
    for tag, commands in registry.items():
        print(f"    {tag}: {list(commands.keys())}")

    test_cases = [
        ("Top-level help", []),
        ("users help", ["users", "--help"]),
        ("users list", ["users", "list", "--limit", "5"]),
        ("users create (flat)", ["users", "create", "--name", "John", "--email", "j@x.com"]),
        ("users create (nested)", ["users", "create", "--name", "John", "--email", "j@x.com", "--address__city", "NYC"]),
        ("users get", ["users", "get", "--user-id", "abc-123"]),
        ("orders list", ["orders", "list"]),
        ("orders create", ["orders", "create", "--customer-id", "cust-1"]),
        ("tags list", ["tags", "list"]),
        ("tags create", ["tags", "create", "--name", "admin"]),
        ("jobs create", ["jobs", "create", "--name", "etl", "--parallelism", "4"]),
        ("users create --help", ["users", "create", "--help"]),
    ]

    for desc, args in test_cases:
        print(f"\n{'='*40}")
        print(f"--- {desc}: mycli {' '.join(args)} ---")
        try:
            dispatch(registry, args)
            print("  [OK]")
        except SystemExit as e:
            if e.code == 0:
                print("  [EXIT 0 - help]")
            else:
                print(f"  [EXIT {e.code}]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    # Benchmark
    print(f"\n{'='*40}")
    print("--- Benchmark ---")
    start = time.perf_counter()
    for _ in range(50):
        dispatch(registry, ["users", "list", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"\n  50 runs: {elapsed:.1f}ms total, {elapsed/50:.1f}ms avg")
