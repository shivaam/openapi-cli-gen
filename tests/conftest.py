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
