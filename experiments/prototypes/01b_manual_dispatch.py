"""
Experiment 1b: Manual dispatch layer on top of pydantic-settings.

We parse the first 1-2 args ourselves (group + command name),
then CliApp.run() handles the flags for that specific command.

Goal: mycli users list --limit 10
      mycli users create --name John --email j@x.com
      mycli orders get --order-id abc
"""

import sys
import time
from pydantic import BaseModel
from pydantic_settings import CliApp


# ============================
# Command models (same as experiment 2 — with nested flattening)
# ============================

class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UsersListCmd(BaseModel):
    """List all users."""
    limit: int = 20
    offset: int = 0
    role: str | None = None

    def cli_cmd(self):
        print(f"GET /users?limit={self.limit}&offset={self.offset}&role={self.role}")


class UsersCreateCmd(BaseModel):
    """Create a new user."""
    name: str
    email: str
    age: int = 25
    role: str = "user"
    address: Address | None = None
    tags: list[str] | None = None

    def cli_cmd(self):
        print(f"POST /users body={self.model_dump_json()}")


class UsersGetCmd(BaseModel):
    """Get a user by ID."""
    user_id: str

    def cli_cmd(self):
        print(f"GET /users/{self.user_id}")


class UsersDeleteCmd(BaseModel):
    """Delete a user."""
    user_id: str

    def cli_cmd(self):
        print(f"DELETE /users/{self.user_id}")


class OrdersListCmd(BaseModel):
    """List all orders."""
    status: str | None = None
    customer_id: str | None = None

    def cli_cmd(self):
        print(f"GET /orders?status={self.status}&customer_id={self.customer_id}")


class OrdersCreateCmd(BaseModel):
    """Create an order."""
    customer_id: str
    notes: str | None = None

    def cli_cmd(self):
        print(f"POST /orders body={self.model_dump_json()}")


class OrdersGetCmd(BaseModel):
    """Get an order by ID."""
    order_id: str

    def cli_cmd(self):
        print(f"GET /orders/{self.order_id}")


class TagsListCmd(BaseModel):
    """List all tags."""
    def cli_cmd(self):
        print("GET /tags")


class TagsCreateCmd(BaseModel):
    """Create a tag."""
    name: str

    def cli_cmd(self):
        print(f"POST /tags body={self.model_dump_json()}")


class JobsCreateCmd(BaseModel):
    """Create a job."""
    name: str
    parallelism: int = 1

    def cli_cmd(self):
        print(f"POST /jobs body={self.model_dump_json()}")


class JobsListCmd(BaseModel):
    """List all jobs."""
    def cli_cmd(self):
        print("GET /jobs")


# ============================
# Registry: maps (group, command) -> model class
# ============================

COMMAND_REGISTRY: dict[str, dict[str, type[BaseModel]]] = {
    "users": {
        "list": UsersListCmd,
        "create": UsersCreateCmd,
        "get": UsersGetCmd,
        "delete": UsersDeleteCmd,
    },
    "orders": {
        "list": OrdersListCmd,
        "create": OrdersCreateCmd,
        "get": OrdersGetCmd,
    },
    "tags": {
        "list": TagsListCmd,
        "create": TagsCreateCmd,
    },
    "jobs": {
        "list": JobsListCmd,
        "create": JobsCreateCmd,
    },
}


def print_help():
    """Print top-level help."""
    print("Usage: mycli <group> <command> [options]")
    print()
    print("Groups:")
    for group, commands in COMMAND_REGISTRY.items():
        cmds = ", ".join(commands.keys())
        print(f"  {group:15} {cmds}")
    print()
    print("Use 'mycli <group> --help' for group help")
    print("Use 'mycli <group> <command> --help' for command help")


def print_group_help(group: str):
    """Print group-level help."""
    commands = COMMAND_REGISTRY[group]
    print(f"Usage: mycli {group} <command> [options]")
    print()
    print("Commands:")
    for cmd_name, cmd_class in commands.items():
        doc = cmd_class.__doc__ or ""
        print(f"  {cmd_name:15} {doc.strip()}")


def dispatch(args: list[str]):
    """Parse group + command, then CliApp.run for flags."""
    if not args or args[0] in ("-h", "--help"):
        print_help()
        return

    group = args[0]
    if group not in COMMAND_REGISTRY:
        print(f"Error: unknown group '{group}'")
        print(f"Available: {', '.join(COMMAND_REGISTRY.keys())}")
        return

    remaining = args[1:]

    if not remaining or remaining[0] in ("-h", "--help"):
        print_group_help(group)
        return

    command = remaining[0]
    if command not in COMMAND_REGISTRY[group]:
        print(f"Error: unknown command '{group} {command}'")
        print(f"Available: {', '.join(COMMAND_REGISTRY[group].keys())}")
        return

    cmd_class = COMMAND_REGISTRY[group][command]
    flag_args = remaining[1:]

    # CliApp.run handles all the flag parsing + validation + execution
    CliApp.run(cmd_class, cli_args=flag_args)


# ============================
# Test runner
# ============================

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 1b: Manual Dispatch + pydantic-settings")
    print("=" * 60)

    test_cases = [
        ("Top-level help", []),
        ("Top-level --help", ["--help"]),
        ("Group help", ["users", "--help"]),
        ("users list", ["users", "list", "--limit", "10"]),
        ("users create (flat)", ["users", "create", "--name", "John", "--email", "j@x.com"]),
        ("users create (nested)", ["users", "create", "--name", "John", "--email", "j@x.com", "--address.city", "NYC"]),
        ("users get", ["users", "get", "--user-id", "abc-123"]),
        ("users delete", ["users", "delete", "--user-id", "abc-123"]),
        ("orders list", ["orders", "list", "--status", "pending"]),
        ("orders create", ["orders", "create", "--customer-id", "cust-1"]),
        ("tags create", ["tags", "create", "--name", "admin"]),
        ("jobs create", ["jobs", "create", "--name", "etl", "--parallelism", "4"]),
        ("Command --help", ["users", "create", "--help"]),
        ("Unknown group", ["widgets"]),
        ("Unknown command", ["users", "frobnicate"]),
    ]

    for desc, args in test_cases:
        print(f"\n--- {desc}: mycli {' '.join(args)} ---")
        try:
            dispatch(args)
            print("  [OK]")
        except SystemExit:
            print("  [EXIT - help shown]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")

    # Benchmark
    print(f"\n--- Benchmark (100 runs) ---")
    start = time.perf_counter()
    for _ in range(100):
        dispatch(["users", "list", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")

    # Benchmark with nested model
    start = time.perf_counter()
    for _ in range(100):
        dispatch(["users", "create", "--name", "John", "--email", "j@x.com", "--address.city", "NYC"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 nested runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")
