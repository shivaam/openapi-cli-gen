"""End-to-end integration tests."""
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
    assert "list" in out or "create" in out or "get" in out


def test_generate_and_load(spec_path, tmp_path, capsys):
    """Generate a package, then verify the generated spec can build a CLI."""
    from openapi_cli_gen.codegen.generator import generate_package

    output = tmp_path / "e2ecli"
    generate_package(spec=str(spec_path), name="e2ecli", output_dir=str(output))

    generated_spec = output / "src" / "e2ecli" / "spec.yaml"
    app = build_cli(spec=str(generated_spec), name="e2ecli")
    try:
        app(["--help"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "users" in out


def test_build_command_group(spec_path):
    """Test build_command_group returns a registry."""
    from openapi_cli_gen import build_command_group

    registry = build_command_group(spec=str(spec_path), name="testcli")
    assert isinstance(registry, dict)
    assert "users" in registry
    assert "orders" in registry
    for group, commands in registry.items():
        for cmd_name, cmd_info in commands.items():
            assert hasattr(cmd_info.model, "cli_cmd")
