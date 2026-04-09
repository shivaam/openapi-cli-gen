"""
Experiment 1c: Typer for command tree, pydantic model flattening done manually.

Goal: mycli users list --limit 10
      mycli users create --name John --email j@x.com --address-city NYC
      mycli orders get --order-id abc

Compare: UX quality (--help, completion) vs manual dispatch approach.
"""

import time
import typer
from typing import Annotated


# ============================
# Typer app with nested command groups
# ============================

app = typer.Typer(help="Test CLI with Typer command tree")

# --- Users group ---
users_app = typer.Typer(help="User management")
app.add_typer(users_app, name="users")


@users_app.command("list")
def users_list(
    limit: Annotated[int, typer.Option(help="Max results")] = 20,
    offset: Annotated[int, typer.Option(help="Skip N results")] = 0,
    role: Annotated[str | None, typer.Option(help="Filter by role")] = None,
):
    """List all users."""
    print(f"GET /users?limit={limit}&offset={offset}&role={role}")


@users_app.command("create")
def users_create(
    name: Annotated[str, typer.Option(help="User name")],
    email: Annotated[str, typer.Option(help="User email")],
    age: Annotated[int, typer.Option(help="User age")] = 25,
    role: Annotated[str, typer.Option(help="User role")] = "user",
    # Flattened nested model — we do this manually
    address_street: Annotated[str | None, typer.Option("--address.street", help="Street")] = None,
    address_city: Annotated[str | None, typer.Option("--address.city", help="City")] = None,
    address_state: Annotated[str | None, typer.Option("--address.state", help="State")] = None,
    address_zip: Annotated[str | None, typer.Option("--address.zip", help="Zip")] = None,
):
    """Create a new user."""
    body = {
        "name": name, "email": email, "age": age, "role": role,
        "address": {"street": address_street, "city": address_city,
                    "state": address_state, "zip": address_zip}
        if any([address_street, address_city, address_state, address_zip])
        else None,
    }
    print(f"POST /users body={body}")


@users_app.command("get")
def users_get(
    user_id: Annotated[str, typer.Option(help="User ID")],
):
    """Get a user by ID."""
    print(f"GET /users/{user_id}")


@users_app.command("delete")
def users_delete(
    user_id: Annotated[str, typer.Option(help="User ID")],
):
    """Delete a user."""
    print(f"DELETE /users/{user_id}")


# --- Orders group ---
orders_app = typer.Typer(help="Order management")
app.add_typer(orders_app, name="orders")


@orders_app.command("list")
def orders_list(
    status: Annotated[str | None, typer.Option(help="Filter by status")] = None,
    customer_id: Annotated[str | None, typer.Option(help="Filter by customer")] = None,
):
    """List all orders."""
    print(f"GET /orders?status={status}&customer_id={customer_id}")


@orders_app.command("create")
def orders_create(
    customer_id: Annotated[str, typer.Option(help="Customer ID")],
    notes: Annotated[str | None, typer.Option(help="Order notes")] = None,
):
    """Create an order."""
    print(f"POST /orders body={{customer_id={customer_id}, notes={notes}}}")


@orders_app.command("get")
def orders_get(
    order_id: Annotated[str, typer.Option(help="Order ID")],
):
    """Get an order by ID."""
    print(f"GET /orders/{order_id}")


# --- Tags group ---
tags_app = typer.Typer(help="Tag management")
app.add_typer(tags_app, name="tags")


@tags_app.command("list")
def tags_list():
    """List all tags."""
    print("GET /tags")


@tags_app.command("create")
def tags_create(
    name: Annotated[str, typer.Option(help="Tag name")],
):
    """Create a tag."""
    print(f"POST /tags body={{name={name}}}")


# --- Jobs group ---
jobs_app = typer.Typer(help="Job management")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("list")
def jobs_list():
    """List all jobs."""
    print("GET /jobs")


@jobs_app.command("create")
def jobs_create(
    name: Annotated[str, typer.Option(help="Job name")],
    parallelism: Annotated[int, typer.Option(help="Parallelism level")] = 1,
):
    """Create a job."""
    print(f"POST /jobs body={{name={name}, parallelism={parallelism}}}")


# ============================
# Test runner (simulates CLI invocations)
# ============================

if __name__ == "__main__":
    from typer.testing import CliRunner

    runner = CliRunner()
    print("=" * 60)
    print("EXPERIMENT 1c: Typer Command Tree")
    print("=" * 60)

    test_cases = [
        ("Top-level --help", ["--help"]),
        ("users --help", ["users", "--help"]),
        ("users list", ["users", "list", "--limit", "10"]),
        ("users create (flat)", ["users", "create", "--name", "John", "--email", "j@x.com"]),
        ("users create (nested)", ["users", "create", "--name", "John", "--email", "j@x.com", "--address.city", "NYC"]),
        ("users get", ["users", "get", "--user-id", "abc-123"]),
        ("users delete", ["users", "delete", "--user-id", "abc-123"]),
        ("orders list", ["orders", "list", "--status", "pending"]),
        ("orders create", ["orders", "create", "--customer-id", "cust-1"]),
        ("tags create", ["tags", "create", "--name", "admin"]),
        ("jobs create", ["jobs", "create", "--name", "etl", "--parallelism", "4"]),
        ("users create --help", ["users", "create", "--help"]),
    ]

    for desc, args in test_cases:
        print(f"\n--- {desc}: mycli {' '.join(args)} ---")
        result = runner.invoke(app, args)
        # Print output, indented
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        if result.exit_code != 0:
            print(f"  [EXIT {result.exit_code}]")
        else:
            print("  [OK]")

    # Benchmark
    print(f"\n--- Benchmark (100 runs) ---")
    start = time.perf_counter()
    for _ in range(100):
        runner.invoke(app, ["users", "list", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")

    start = time.perf_counter()
    for _ in range(100):
        runner.invoke(app, ["users", "create", "--name", "John", "--email", "j@x.com", "--address.city", "NYC"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 nested runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")
