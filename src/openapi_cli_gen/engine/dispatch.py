from __future__ import annotations

import sys

import httpx
from pydantic_settings import CliApp

from openapi_cli_gen.engine.registry import CommandInfo


def dispatch(
    registry: dict[str, dict[str, CommandInfo]],
    args: list[str],
    name: str = "cli",
) -> None:
    """Dispatch CLI args to the right command via manual group+command routing."""
    if not args or args[0] in ("-h", "--help"):
        _print_root_help(registry, name)
        return

    group = args[0]
    if group not in registry:
        print(f"Error: unknown group '{group}'. Available: {', '.join(sorted(registry.keys()))}")
        sys.exit(1)

    remaining = args[1:]
    if not remaining or remaining[0] in ("-h", "--help"):
        _print_group_help(registry[group], group, name)
        return

    command = remaining[0]
    if command not in registry[group]:
        print(f"Error: unknown command '{group} {command}'. Available: {', '.join(sorted(registry[group].keys()))}")
        sys.exit(1)

    cmd_info = registry[group][command]
    flag_args = remaining[1:]

    try:
        CliApp.run(cmd_info.model, cli_args=flag_args)
    except httpx.ConnectError as e:
        # Typo'd base URL or stopped service. Give users a one-line hint
        # instead of a 60-line httpx/pydantic_settings traceback.
        prefix = name.upper().replace("-", "_")
        print(
            f"Error: could not connect to the API server. "
            f"Is the service running and is {prefix}_BASE_URL set correctly?\n"
            f"Details: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except httpx.ConnectTimeout as e:
        print(f"Error: connection timed out. Check {name.upper().replace('-', '_')}_BASE_URL and network.\nDetails: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.ReadTimeout as e:
        print(f"Error: the server took too long to respond.\nDetails: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPError as e:
        # Catch-all for other httpx transport errors (DNS resolution, TLS, etc.)
        print(f"Error: HTTP transport failed.\nDetails: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


def _print_root_help(
    registry: dict[str, dict[str, CommandInfo]],
    name: str,
) -> None:
    print(f"Usage: {name} <group> <command> [options]\n")
    print("Groups:")
    for group, commands in sorted(registry.items()):
        cmds = ", ".join(sorted(commands.keys()))
        print(f"  {group:20} {cmds}")
    print(f"\nUse '{name} <group> --help' for group help")


def _print_group_help(
    commands: dict[str, CommandInfo],
    group: str,
    name: str,
) -> None:
    print(f"Usage: {name} {group} <command> [options]\n")
    print("Commands:")
    for cmd_name, cmd_info in sorted(commands.items()):
        doc = cmd_info.endpoint.summary or cmd_info.endpoint.operation_id
        print(f"  {cmd_name:20} {doc}")
