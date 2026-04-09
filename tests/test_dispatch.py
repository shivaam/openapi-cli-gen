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
