from __future__ import annotations

import typer

from openapi_cli_gen.spec.loader import load_spec
from openapi_cli_gen.spec.parser import parse_spec, extract_security_schemes

app = typer.Typer(
    name="openapi-cli-gen",
    help="Generate typed Python CLIs from OpenAPI specs.",
)


@app.command()
def generate(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file"),
    name: str = typer.Option(..., help="CLI/package name"),
    output: str = typer.Option(None, help="Output directory (default: ./<name>)"),
):
    """Generate a CLI package from an OpenAPI spec."""
    from openapi_cli_gen.codegen.generator import generate_package

    output_dir = output or f"./{name}"
    result = generate_package(spec=spec, name=name, output_dir=output_dir)
    typer.echo(f"Generated CLI package at: {result}")


@app.command(
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False},
)
def run(
    ctx: typer.Context,
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
    base_url: str = typer.Option(None, help="Override API base URL"),
):
    """Run a CLI directly from an OpenAPI spec (no code generation)."""
    from openapi_cli_gen import build_cli

    cli = build_cli(spec=spec, name="cli", base_url=base_url)
    cli(ctx.args or [])


@app.command()
def inspect(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file"),
):
    """Inspect an OpenAPI spec — show what would be generated."""
    resolved = load_spec(spec)
    endpoints = parse_spec(resolved)
    schemes = extract_security_schemes(resolved)

    groups: dict[str, list] = {}
    for ep in endpoints:
        groups.setdefault(ep.tag, []).append(ep)

    title = resolved.get("info", {}).get("title", "Unknown")
    version = resolved.get("info", {}).get("version", "?")

    typer.echo(f"API: {title} v{version}")
    typer.echo(f"Endpoints: {len(endpoints)}")
    typer.echo(f"Groups: {len(groups)}")
    typer.echo(f"Auth schemes: {len(schemes)}")
    typer.echo()

    for group_name, eps in sorted(groups.items()):
        typer.echo(f"  {group_name}:")
        for ep in eps:
            body = " [body]" if ep.body_schema else ""
            typer.echo(f"    {ep.method.upper():7} {ep.path:30} {ep.summary}{body}")


def main():
    app()
