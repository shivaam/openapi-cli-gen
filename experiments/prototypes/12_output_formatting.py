"""
Experiment 12: Output formatting — JSON, table, YAML.

Prototype the formatter that will render API responses.
"""

import json
import yaml
from rich.console import Console
from rich.table import Table


# Sample API responses
SINGLE_USER = {
    "id": "usr_123",
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30,
    "role": "admin",
    "address": {"city": "NYC", "state": "NY"},
    "tags": ["dev", "lead"],
    "created_at": "2026-04-08T10:00:00Z",
}

USER_LIST = {
    "items": [
        {"id": "usr_123", "name": "John Doe", "email": "john@example.com", "age": 30, "role": "admin"},
        {"id": "usr_456", "name": "Jane Smith", "email": "jane@example.com", "age": 28, "role": "user"},
        {"id": "usr_789", "name": "Bob Wilson", "email": "bob@example.com", "age": 35, "role": "viewer"},
    ],
    "total": 3,
}

NESTED_ORDER = {
    "id": "ord_001",
    "customer_id": "cust_1",
    "items": [
        {"product_id": "prod_a", "quantity": 2, "price": 9.99},
        {"product_id": "prod_b", "quantity": 1, "price": 24.99},
    ],
    "total": 44.97,
    "status": "pending",
}


def format_json(data: dict | list, pretty: bool = True) -> str:
    """Format as JSON."""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)


def format_yaml(data: dict | list) -> str:
    """Format as YAML."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def format_table(data: dict | list) -> None:
    """Format as a rich table. Handles single object, list, and wrapped lists."""
    console = Console()

    # Detect list data
    rows = None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        # Check for common wrapper patterns: items, results, data
        for key in ("items", "results", "data"):
            if key in data and isinstance(data[key], list):
                rows = data[key]
                # Show metadata
                for k, v in data.items():
                    if k != key:
                        console.print(f"[dim]{k}:[/dim] {v}")
                break

    if rows and len(rows) > 0:
        # Build table from list of dicts
        table = Table(show_header=True, header_style="bold")
        keys = list(rows[0].keys())
        for key in keys:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row.get(k, "")) for k in keys])
        console.print(table)
    elif isinstance(data, dict):
        # Single object — key/value table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Field")
        table.add_column("Value")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            table.add_row(str(key), str(value))
        console.print(table)
    else:
        console.print(data)


def format_output(data: dict | list, fmt: str = "json"):
    """Main formatter dispatcher."""
    if fmt == "json":
        print(format_json(data))
    elif fmt == "yaml":
        print(format_yaml(data))
    elif fmt == "table":
        format_table(data)
    elif fmt == "raw":
        print(data)
    else:
        print(f"Unknown format: {fmt}")


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 12: Output Formatting")
    print("=" * 60)

    test_data = [
        ("Single user", SINGLE_USER),
        ("User list (wrapped)", USER_LIST),
        ("Order (nested)", NESTED_ORDER),
        ("Plain list", USER_LIST["items"]),
    ]

    for desc, data in test_data:
        for fmt in ("json", "yaml", "table"):
            print(f"\n--- {desc} as {fmt} ---")
            try:
                format_output(data, fmt)
                print("  [OK]")
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {e}")
