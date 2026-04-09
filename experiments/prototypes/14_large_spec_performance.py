"""
Experiment 14: Performance with large specs.

Simulate: 50, 100, 200, 500 endpoints across 10-20 tags.
Measure: spec parse time, model creation time, dispatch lookup time.
"""

import time
import json
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_settings import CliApp


def generate_large_spec(n_endpoints: int, n_tags: int = 10) -> dict:
    """Generate a synthetic OpenAPI spec with N endpoints."""
    paths = {}
    schemas = {}

    for i in range(n_endpoints):
        tag = f"resource{i % n_tags}"
        verb = ["get", "post", "put", "delete"][i % 4]
        path = f"/{tag}/{i}"

        # Create a schema for POST/PUT bodies
        schema_name = f"Body{i}"
        schemas[schema_name] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"},
                "description": {"type": "string"},
                "nested": {
                    "type": "object",
                    "properties": {
                        "field_a": {"type": "string"},
                        "field_b": {"type": "integer"},
                    },
                },
            },
            "required": ["name"],
        }

        operation = {
            "operationId": f"{verb}_{tag}_{i}",
            "tags": [tag],
            "summary": f"Operation {i}",
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
            ],
        }

        if verb in ("post", "put"):
            operation["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": schemas[schema_name]
                    }
                }
            }

        if path not in paths:
            paths[path] = {}
        paths[path][verb] = operation

    return {
        "openapi": "3.1.0",
        "info": {"title": f"Large API ({n_endpoints} endpoints)", "version": "1.0"},
        "paths": paths,
        "components": {"schemas": schemas},
    }


def build_registry_from_spec(spec: dict) -> dict:
    """Build command registry (simulating our engine)."""
    registry = {}
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "delete"):
                continue

            tag = operation["tags"][0]
            op_id = operation["operationId"]

            # Build fields
            fields = {}
            for p in operation.get("parameters", []):
                ptype = {"string": str, "integer": int}.get(p["schema"]["type"], str)
                if p.get("required"):
                    fields[p["name"]] = (ptype, FieldInfo())
                else:
                    default = p["schema"].get("default")
                    fields[p["name"]] = (ptype | None, FieldInfo(default=default))

            # Body fields (flat — just top level for perf test)
            rb = operation.get("requestBody", {})
            body_schema = rb.get("content", {}).get("application/json", {}).get("schema", {})
            for fname, fprop in body_schema.get("properties", {}).items():
                if fprop.get("type") == "object":
                    continue  # skip nested for perf test
                ptype = {"string": str, "integer": int}.get(fprop.get("type"), str)
                req = fname in body_schema.get("required", [])
                if req:
                    fields[fname] = (ptype, FieldInfo())
                else:
                    fields[fname] = (ptype | None, FieldInfo(default=None))

            model = create_model(f"Cmd_{op_id}", **fields) if fields else create_model(f"Cmd_{op_id}")

            registry.setdefault(tag, {})[op_id] = model

    return registry


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 14: Large Spec Performance")
    print("=" * 60)

    for n in [14, 50, 100, 200, 500]:
        print(f"\n--- {n} endpoints ---")

        # Generate spec
        start = time.perf_counter()
        spec = generate_large_spec(n)
        gen_time = (time.perf_counter() - start) * 1000

        # Build registry
        start = time.perf_counter()
        registry = build_registry_from_spec(spec)
        build_time = (time.perf_counter() - start) * 1000

        n_groups = len(registry)
        n_commands = sum(len(cmds) for cmds in registry.values())

        print(f"  Spec gen:  {gen_time:.1f}ms")
        print(f"  Registry:  {build_time:.1f}ms ({n_groups} groups, {n_commands} commands)")

        # Dispatch lookup (dict lookup — should be O(1))
        first_group = list(registry.keys())[0]
        first_cmd = list(registry[first_group].keys())[0]
        model = registry[first_group][first_cmd]

        # Add cli_cmd
        model.cli_cmd = lambda self: None

        start = time.perf_counter()
        for _ in range(100):
            CliApp.run(model, cli_args=["--id", "test", "--limit", "5"])
        run_time = (time.perf_counter() - start) * 1000

        print(f"  100 runs:  {run_time:.1f}ms ({run_time/100:.2f}ms avg)")
        print(f"  Total startup: {gen_time + build_time:.1f}ms")
