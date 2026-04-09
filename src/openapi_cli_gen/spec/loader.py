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
