"""
Experiment 1: Can pydantic-settings handle a multi-command tree?

Finding from first attempt: 3-level nesting (root → group → command) via
CliSubCommand fails with KeyError in run_subcommand. Testing alternative approaches.
"""

import time
from pydantic import BaseModel
from pydantic_settings import BaseSettings, CliApp, CliSubCommand


# ============================
# Approach A: 2-level only (root → command)
# No groups, flat list of commands
# ============================

class UsersListCmd(BaseModel):
    """List all users."""
    limit: int = 20
    offset: int = 0
    def cli_cmd(self):
        print(f"users-list: limit={self.limit} offset={self.offset}")

class UsersCreateCmd(BaseModel):
    """Create a new user."""
    name: str
    email: str
    age: int = 25
    def cli_cmd(self):
        print(f"users-create: name={self.name} email={self.email} age={self.age}")

class UsersGetCmd(BaseModel):
    """Get a user by ID."""
    user_id: str
    def cli_cmd(self):
        print(f"users-get: user_id={self.user_id}")

class OrdersListCmd(BaseModel):
    """List all orders."""
    status: str | None = None
    def cli_cmd(self):
        print(f"orders-list: status={self.status}")

class OrdersCreateCmd(BaseModel):
    """Create an order."""
    customer_id: str
    def cli_cmd(self):
        print(f"orders-create: customer_id={self.customer_id}")

class TagsCreateCmd(BaseModel):
    """Create a tag."""
    name: str
    def cli_cmd(self):
        print(f"tags-create: name={self.name}")

class JobsCreateCmd(BaseModel):
    """Create a job."""
    name: str
    parallelism: int = 1
    def cli_cmd(self):
        print(f"jobs-create: name={self.name} parallelism={self.parallelism}")


# Flat: all commands at one level
class FlatCLI(BaseModel):
    """Flat CLI — all commands at root level."""
    command: CliSubCommand[
        UsersListCmd | UsersCreateCmd | UsersGetCmd
        | OrdersListCmd | OrdersCreateCmd
        | TagsCreateCmd | JobsCreateCmd
    ]
    def cli_cmd(self):
        CliApp.run_subcommand(self)


# ============================
# Approach B: Named fields per group (not Union, individual fields)
# ============================

class UsersGroup(BaseModel):
    """User management."""
    command: CliSubCommand[UsersListCmd | UsersCreateCmd | UsersGetCmd]
    def cli_cmd(self):
        CliApp.run_subcommand(self)

class OrdersGroup(BaseModel):
    """Order management."""
    command: CliSubCommand[OrdersListCmd | OrdersCreateCmd]
    def cli_cmd(self):
        CliApp.run_subcommand(self)

class NamedFieldCLI(BaseModel):
    """Named field CLI — each group is a separate field."""
    users: CliSubCommand[UsersGroup] | None = None
    orders: CliSubCommand[OrdersGroup] | None = None

    def cli_cmd(self):
        CliApp.run_subcommand(self)


# ============================
# Approach C: Separate CliApp.run per group
# Build our own dispatch instead of nested CliSubCommand
# ============================

import sys

def approach_c_dispatch():
    """Manual dispatch: parse first arg, then CliApp.run the right group."""
    if len(sys.argv) < 2:
        print("Usage: mycli <group> <command> [options]")
        print("Groups: users, orders, tags, jobs")
        return

    group = sys.argv[1]
    remaining = sys.argv[2:]

    groups = {
        "users": UsersGroup,
        "orders": OrdersGroup,
    }

    if group in groups:
        CliApp.run(groups[group], cli_args=remaining)
    else:
        print(f"Unknown group: {group}")


# ============================
# Test runner
# ============================

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 1: pydantic-settings Multi-Command Tree")
    print("=" * 60)

    # --- Test Approach A: Flat ---
    print("\n### APPROACH A: Flat (all commands at root) ###")
    flat_tests = [
        ("--help", ["--help"]),
        ("UsersListCmd", ["UsersListCmd", "--limit", "10"]),
        ("UsersCreateCmd", ["UsersCreateCmd", "--name", "John", "--email", "j@x.com"]),
        ("UsersGetCmd", ["UsersGetCmd", "--user-id", "abc"]),
        ("OrdersListCmd", ["OrdersListCmd", "--status", "pending"]),
        ("TagsCreateCmd", ["TagsCreateCmd", "--name", "admin"]),
        ("JobsCreateCmd", ["JobsCreateCmd", "--name", "etl", "--parallelism", "4"]),
    ]
    for desc, args in flat_tests:
        print(f"\n  --- {desc} ---")
        try:
            CliApp.run(FlatCLI, cli_args=args)
            print("  [OK]")
        except SystemExit:
            print("  [EXIT - help/error]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")

    # --- Test Approach B: Named fields ---
    print("\n\n### APPROACH B: Named fields per group ###")
    named_tests = [
        ("--help", ["--help"]),
        ("users --help", ["users", "--help"]),
        ("users UsersListCmd", ["users", "UsersListCmd", "--limit", "10"]),
        ("users UsersCreateCmd", ["users", "UsersCreateCmd", "--name", "John", "--email", "j@x.com"]),
        ("orders OrdersListCmd", ["orders", "OrdersListCmd", "--status", "pending"]),
    ]
    for desc, args in named_tests:
        print(f"\n  --- {desc} ---")
        try:
            CliApp.run(NamedFieldCLI, cli_args=args)
            print("  [OK]")
        except SystemExit:
            print("  [EXIT - help/error]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")

    # --- Benchmark ---
    print("\n\n### BENCHMARK ###")
    # Approach A
    start = time.perf_counter()
    for _ in range(100):
        CliApp.run(FlatCLI, cli_args=["UsersListCmd", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Flat (100 runs): {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")

    # Approach B
    start = time.perf_counter()
    for _ in range(100):
        CliApp.run(NamedFieldCLI, cli_args=["users", "UsersListCmd", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Named (100 runs): {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")
