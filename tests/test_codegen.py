from pathlib import Path
from openapi_cli_gen.codegen.generator import generate_package


def test_generate_creates_directory(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    assert output.exists()
    assert (output / "pyproject.toml").exists()


def test_generate_creates_cli_py(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    cli_py = output / "src" / "mycli" / "cli.py"
    assert cli_py.exists()
    content = cli_py.read_text()
    assert "build_cli" in content
    assert "mycli" in content


def test_generate_copies_spec(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    spec = output / "src" / "mycli" / "spec.yaml"
    assert spec.exists()


def test_generate_creates_pyproject(spec_path, tmp_path):
    output = tmp_path / "mycli"
    generate_package(spec=str(spec_path), name="mycli", output_dir=str(output))
    pyproject = output / "pyproject.toml"
    content = pyproject.read_text()
    assert "mycli" in content
    assert "openapi-cli-gen" in content
