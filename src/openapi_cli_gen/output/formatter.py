from __future__ import annotations

import json

import yaml
from rich.console import Console
from rich.table import Table


def format_output(
    data: dict | list,
    fmt: str = "json",
    print_output: bool = False,
) -> str | None:
    """Format API response data for CLI output."""
    if fmt == "json":
        result = json.dumps(data, indent=2, default=str)
    elif fmt == "yaml":
        result = yaml.dump(data, default_flow_style=False, sort_keys=False)
    elif fmt == "raw":
        result = str(data)
    elif fmt == "table":
        _print_table(data)
        return None
    else:
        result = json.dumps(data, indent=2, default=str)

    if print_output:
        print(result)
    return result


def _print_table(data: dict | list) -> None:
    """Print data as a rich table."""
    console = Console()
    rows = None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        for key in ("items", "results", "data"):
            if key in data and isinstance(data[key], list):
                rows = data[key]
                for k, v in data.items():
                    if k != key:
                        console.print(f"[dim]{k}:[/dim] {v}")
                break

    if rows and len(rows) > 0:
        table = Table(show_header=True, header_style="bold")
        keys = list(rows[0].keys())
        for key in keys:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row.get(k, "")) for k in keys])
        console.print(table)
    elif isinstance(data, dict):
        table = Table(show_header=True, header_style="bold")
        table.add_column("Field")
        table.add_column("Value")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            table.add_row(str(key), str(value))
        console.print(table)
    else:
        console.print(str(data))
