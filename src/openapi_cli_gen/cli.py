from __future__ import annotations

import typer

from openapi_cli_gen.spec.loader import load_spec
from openapi_cli_gen.spec.parser import parse_spec, extract_security_schemes

app = typer.Typer(
    name="openapi-cli-gen",
    help="Generate typed Python CLIs from OpenAPI specs.",
)


def _resolve_ssl_options(
    verify_ssl: bool,
    ca_cert: str | None,
    client_cert: str | None,
    client_key: str | None,
) -> tuple[bool | str, tuple[str, str] | str | None]:
    """Map the user-facing SSL flags to httpx's (verify, cert) shape."""
    if not verify_ssl:
        verify: bool | str = False
    elif ca_cert:
        verify = ca_cert
    else:
        verify = True

    cert: tuple[str, str] | str | None
    if client_cert and client_key:
        cert = (client_cert, client_key)
    elif client_cert:
        cert = client_cert
    else:
        cert = None
    return verify, cert


@app.command()
def generate(
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
    name: str = typer.Option(..., help="CLI/package name"),
    output: str = typer.Option(None, help="Output directory (default: ./<name>)"),
    base_url: str = typer.Option(None, help="Default API base URL for the generated CLI"),
    description: str = typer.Option(None, help="PyPI project description (shown on the package page)"),
    verify_ssl: bool = typer.Option(True, "--verify-ssl/--no-verify-ssl", help="Verify SSL certs when downloading the spec from an HTTPS URL"),
    ca_cert: str = typer.Option(None, help="Path to a CA bundle to use when fetching the spec"),
    client_cert: str = typer.Option(None, help="Path to a client certificate (PEM) for mTLS"),
    client_key: str = typer.Option(None, help="Path to the client certificate key (PEM)"),
    version: str = typer.Option("0.1.0", "--wrapper-version", help="Version for the generated package"),
):
    """Generate a CLI package from an OpenAPI spec."""
    from openapi_cli_gen.codegen.generator import generate_package

    verify, cert = _resolve_ssl_options(verify_ssl, ca_cert, client_cert, client_key)

    output_dir = output or f"./{name}"
    result = generate_package(
        spec=spec,
        name=name,
        output_dir=output_dir,
        base_url=base_url,
        description=description,
        verify_ssl=verify,
        client_cert=cert,
        wrapper_version=version,
    )
    typer.echo(f"Generated CLI package at: {result}")


@app.command(
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False},
)
def run(
    ctx: typer.Context,
    spec: str = typer.Option(..., help="Path to OpenAPI spec file or URL"),
    base_url: str = typer.Option(None, help="Override API base URL"),
    verify_ssl: bool = typer.Option(True, "--verify-ssl/--no-verify-ssl", help="Verify SSL certs for spec download and API calls"),
    ca_cert: str = typer.Option(None, help="Path to a CA bundle for HTTPS verification"),
    client_cert: str = typer.Option(None, help="Path to a client certificate (PEM) for mTLS"),
    client_key: str = typer.Option(None, help="Path to the client certificate key (PEM)"),
):
    """Run a CLI directly from an OpenAPI spec (no code generation)."""
    from openapi_cli_gen import build_cli

    verify, cert = _resolve_ssl_options(verify_ssl, ca_cert, client_cert, client_key)
    cli = build_cli(
        spec=spec, name="cli", base_url=base_url,
        verify_ssl=verify, client_cert=cert,
    )
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
