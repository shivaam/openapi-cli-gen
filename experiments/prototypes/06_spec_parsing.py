"""
Experiment 6: Does jsonref + openapi-pydantic work end-to-end on our test spec?
"""

import time
import json
from pathlib import Path

import yaml
import jsonref


def test_jsonref():
    """Test jsonref $ref resolution."""
    print("\n--- jsonref $ref resolution ---")
    spec_path = Path(__file__).parent.parent / "server" / "spec.yaml"
    raw = yaml.safe_load(spec_path.read_text())

    start = time.perf_counter()
    resolved = jsonref.replace_refs(raw)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Resolved in {elapsed:.1f}ms")

    # Check that $ref is resolved
    user_create_schema = resolved["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    print(f"  UserCreate type: {user_create_schema.get('type')}")
    print(f"  UserCreate properties: {list(user_create_schema.get('properties', {}).keys())}")

    # Check nested ref (address inside UserCreate)
    address = user_create_schema["properties"]["address"]
    print(f"  Address resolved? {address.get('type', 'NO TYPE')} - props: {list(address.get('properties', {}).keys())}")

    # Check discriminated union
    notification = resolved["paths"]["/notifications"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    print(f"  Notification oneOf count: {len(notification.get('oneOf', []))}")
    print(f"  Notification discriminator: {notification.get('discriminator', {}).get('propertyName')}")

    return resolved


def test_openapi_pydantic(resolved):
    """Test openapi-pydantic typed parsing."""
    print("\n--- openapi-pydantic typed parsing ---")

    try:
        from openapi_pydantic import parse_obj
        start = time.perf_counter()
        spec = parse_obj(resolved)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Parsed in {elapsed:.1f}ms")

        # Test typed access
        print(f"  Title: {spec.info.title}")
        print(f"  Version: {spec.info.version}")
        print(f"  Paths count: {len(spec.paths)}")
        print(f"  Schemas count: {len(spec.components.schemas)}")

        # Iterate endpoints
        print(f"\n  Endpoints:")
        for path, path_item in spec.paths.items():
            for method_name in ["get", "post", "put", "delete", "patch"]:
                operation = getattr(path_item, method_name, None)
                if operation:
                    tags = operation.tags or ["untagged"]
                    params = operation.parameters or []
                    has_body = operation.requestBody is not None
                    print(f"    {method_name.upper():6} {path:30} tag={tags[0]:15} operationId={operation.operationId or 'none':25} params={len(params)} body={has_body}")

        # Test security schemes
        print(f"\n  Security schemes:")
        if spec.components and spec.components.securitySchemes:
            for name, scheme in spec.components.securitySchemes.items():
                print(f"    {name}: type={scheme.type}, scheme={getattr(scheme, 'scheme', 'N/A')}")

        return spec

    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_extract_command_info(spec):
    """Test extracting CLI-relevant info from parsed spec."""
    print("\n--- Extract command info ---")

    commands_by_tag = {}
    for path, path_item in spec.paths.items():
        for method_name in ["get", "post", "put", "delete", "patch"]:
            operation = getattr(path_item, method_name, None)
            if not operation:
                continue

            tag = (operation.tags or ["default"])[0]
            op_id = operation.operationId or f"{method_name}_{path}"

            # Extract path params
            path_params = []
            query_params = []
            if operation.parameters:
                for p in operation.parameters:
                    if hasattr(p, 'param_in'):
                        if str(p.param_in) == "ParameterLocation.PATH" or "path" in str(p.param_in).lower():
                            path_params.append(p.name)
                        elif str(p.param_in) == "ParameterLocation.QUERY" or "query" in str(p.param_in).lower():
                            query_params.append(p.name)

            # Extract body schema
            body_schema = None
            if operation.requestBody:
                content = operation.requestBody.content or {}
                json_content = content.get("application/json")
                if json_content and json_content.media_type_schema:
                    body_schema = json_content.media_type_schema

            if tag not in commands_by_tag:
                commands_by_tag[tag] = []

            commands_by_tag[tag].append({
                "operation_id": op_id,
                "method": method_name,
                "path": path,
                "path_params": path_params,
                "query_params": query_params,
                "has_body": body_schema is not None,
            })

    for tag, commands in commands_by_tag.items():
        print(f"\n  {tag}:")
        for cmd in commands:
            print(f"    {cmd['operation_id']:25} {cmd['method'].upper():6} {cmd['path']:30} path_params={cmd['path_params']} query_params={cmd['query_params']} body={cmd['has_body']}")


def test_circular_ref():
    """Test circular $ref handling."""
    print("\n--- Circular $ref test ---")
    circular_spec = {
        "openapi": "3.1.0",
        "info": {"title": "Circular Test", "version": "0.1"},
        "components": {
            "schemas": {
                "TreeNode": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/TreeNode"},
                        },
                    },
                }
            }
        },
        "paths": {},
    }

    try:
        resolved = jsonref.replace_refs(circular_spec)
        # Access the circular ref
        node = resolved["components"]["schemas"]["TreeNode"]
        child_items = node["properties"]["children"]["items"]
        print(f"  TreeNode resolved: {list(node['properties'].keys())}")
        print(f"  Child items type: {type(child_items).__name__}")
        # Try to access deeper (should work with lazy proxies)
        deeper = child_items["properties"]["children"]["items"]
        print(f"  Deeper access works: {type(deeper).__name__}")
        print("  [OK] Circular refs handled via lazy proxies")
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 6: Spec Parsing Pipeline")
    print("=" * 60)

    resolved = test_jsonref()
    spec = test_openapi_pydantic(resolved)
    if spec:
        test_extract_command_info(spec)
    test_circular_ref()
