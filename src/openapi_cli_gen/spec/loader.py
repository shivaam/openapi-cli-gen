from __future__ import annotations

import json
from pathlib import Path

import httpx
import jsonref
import yaml


def load_spec(spec_path: str) -> dict:
    """Load an OpenAPI spec from a file path or URL, resolve all $ref references.

    Args:
        spec_path: Path to YAML/JSON file, or HTTP(S) URL to an OpenAPI spec.

    Returns:
        Fully resolved spec as a dict (all $ref inlined).

    Raises:
        FileNotFoundError: If local spec file does not exist.
        httpx.HTTPError: If URL fetch fails.
    """
    if spec_path.startswith(("http://", "https://")):
        return _load_from_url(spec_path)
    return _load_from_file(spec_path)


def load_raw_spec(spec_path: str) -> dict:
    """Load an OpenAPI spec from a file path or URL WITHOUT resolving refs.

    Used to extract $ref names before resolution.
    """
    if spec_path.startswith(("http://", "https://")):
        resp = httpx.get(spec_path, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        text = resp.text
        if spec_path.endswith((".yaml", ".yml")):
            return yaml.safe_load(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return yaml.safe_load(text)

    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    text = path.read_text()
    if path.suffix in (".json",):
        return json.loads(text)
    return yaml.safe_load(text)


def extract_body_schema_names(raw_spec: dict) -> dict[tuple[str, str], str]:
    """Extract the $ref schema name for each endpoint's request body.

    Returns: {(path, method): schema_name}
    """
    result = {}
    for path, path_item in raw_spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            op = path_item.get(method)
            if not op:
                continue
            rb = op.get("requestBody")
            if not rb:
                continue
            content = rb.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            ref = schema.get("$ref")
            if ref and ref.startswith("#/components/schemas/"):
                name = ref.split("/")[-1]
                result[(path, method)] = name
    return result


def _load_from_file(spec_path: str) -> dict:
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


def _load_from_url(url: str) -> dict:
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    text = resp.text

    if "json" in content_type or url.endswith(".json"):
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)

    return jsonref.replace_refs(raw, base_uri=url)
