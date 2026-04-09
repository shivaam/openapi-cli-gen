from pathlib import Path
from openapi_cli_gen.spec.loader import load_spec


def test_load_yaml_file(spec_path):
    result = load_spec(str(spec_path))
    assert result["openapi"] == "3.1.0"
    assert "paths" in result
    assert "/users" in result["paths"]


def test_load_resolves_refs(spec_path):
    result = load_spec(str(spec_path))
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
