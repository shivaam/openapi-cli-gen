from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader

import openapi_cli_gen


def generate_package(
    spec: str,
    name: str,
    output_dir: str,
) -> Path:
    """Generate a CLI package from an OpenAPI spec."""
    output = Path(output_dir)
    pkg_dir = output / "src" / name

    pkg_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=PackageLoader("openapi_cli_gen", "codegen/templates"),
        keep_trailing_newline=True,
    )

    context = {
        "name": name,
        "openapi_cli_gen_version": openapi_cli_gen.__version__,
    }

    for template_name, output_path in [
        ("cli.py.jinja2", pkg_dir / "cli.py"),
        ("__init__.py.jinja2", pkg_dir / "__init__.py"),
        ("pyproject.toml.jinja2", output / "pyproject.toml"),
    ]:
        template = env.get_template(template_name)
        output_path.write_text(template.render(**context))

    # Copy or download the spec file
    spec_dest = pkg_dir / "spec.yaml"
    if spec.startswith(("http://", "https://")):
        import httpx
        resp = httpx.get(spec, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        spec_dest.write_text(resp.text)
    else:
        shutil.copy2(spec, spec_dest)

    return output
