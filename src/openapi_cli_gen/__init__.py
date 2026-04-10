"""Generate typed Python CLIs from OpenAPI specs with Pydantic model flattening."""

__version__ = "0.0.6"

from openapi_cli_gen.engine.builder import build_cli, build_command_group

__all__ = ["build_cli", "build_command_group", "__version__"]
