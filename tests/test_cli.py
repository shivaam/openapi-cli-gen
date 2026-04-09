import subprocess
import sys
from pathlib import Path

SPEC_PATH = str(Path(__file__).parent.parent / "experiments" / "server" / "spec.yaml")


def _run_cli(*args):
    result = subprocess.run(
        [sys.executable, "-m", "openapi_cli_gen", *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    return result


def test_cli_help():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "generate" in result.stdout
    assert "run" in result.stdout
    assert "inspect" in result.stdout


def test_inspect_command():
    result = _run_cli("inspect", "--spec", SPEC_PATH)
    assert result.returncode == 0
    output = result.stdout.lower()
    assert "endpoint" in output or "group" in output
