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
    assert "list" in user_cmds
    assert "create" in user_cmds


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
    users = registry["users"]
    create_cmd = users.get("create")
    assert create_cmd is not None
    fields = create_cmd.model.model_fields
    assert "name" in fields
    assert "email" in fields
