"""
Experiment 3: How do arrays and dicts work in pydantic-settings CLI?

Tests: list[str], list[int], list[Object], dict[str,str], enums
"""

from enum import Enum
from pydantic import BaseModel
from pydantic_settings import CliApp


# === Array of primitives ===

class TagsCmd(BaseModel):
    """Test array of strings."""
    name: str
    tags: list[str] | None = None

    def cli_cmd(self):
        print(f"tags={self.tags}")


class ScoresCmd(BaseModel):
    """Test array of ints."""
    name: str
    scores: list[int] | None = None

    def cli_cmd(self):
        print(f"scores={self.scores}")


# === Array of objects ===

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float | None = None


class OrderCmd(BaseModel):
    """Test array of objects."""
    customer_id: str
    items: list[OrderItem]
    notes: str | None = None

    def cli_cmd(self):
        print(f"Order: {self.model_dump_json(indent=2)}")


# === Dict ===

class EnvCmd(BaseModel):
    """Test dict field."""
    name: str
    environment: dict[str, str] | None = None
    labels: dict[str, str] | None = None

    def cli_cmd(self):
        print(f"Env: {self.model_dump_json(indent=2)}")


# === Enum ===

class Role(str, Enum):
    admin = "admin"
    user = "user"
    viewer = "viewer"


class EnumCmd(BaseModel):
    """Test enum field."""
    name: str
    role: Role = Role.user

    def cli_cmd(self):
        print(f"name={self.name} role={self.role.value}")


# === Mixed ===

class Address(BaseModel):
    city: str | None = None
    state: str | None = None


class ComplexCmd(BaseModel):
    """Test everything together."""
    name: str
    role: Role = Role.user
    tags: list[str] | None = None
    address: Address | None = None
    metadata: dict[str, str] | None = None

    def cli_cmd(self):
        print(f"Complex: {self.model_dump_json(indent=2)}")


# ============================
# Test runner
# ============================

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 3: Arrays, Dicts, Enums")
    print("=" * 60)

    tests = [
        # --- Array of strings ---
        ("str[] --help", TagsCmd, ["--help"]),
        ("str[] repeated flags", TagsCmd, ["--name", "x", "--tags", "admin", "--tags", "reviewer"]),
        ("str[] JSON", TagsCmd, ["--name", "x", "--tags", '["admin", "reviewer"]']),
        ("str[] comma-separated", TagsCmd, ["--name", "x", "--tags", "admin,reviewer"]),
        ("str[] empty", TagsCmd, ["--name", "x"]),

        # --- Array of ints ---
        ("int[] repeated", ScoresCmd, ["--name", "x", "--scores", "10", "--scores", "20", "--scores", "30"]),
        ("int[] JSON", ScoresCmd, ["--name", "x", "--scores", "[10, 20, 30]"]),

        # --- Array of objects ---
        ("obj[] --help", OrderCmd, ["--help"]),
        ("obj[] JSON array", OrderCmd, [
            "--customer-id", "cust-1",
            "--items", '[{"product_id": "abc", "quantity": 2, "price": 9.99}]'
        ]),
        ("obj[] repeated JSON", OrderCmd, [
            "--customer-id", "cust-1",
            "--items", '{"product_id": "abc", "quantity": 2}',
            "--items", '{"product_id": "def", "quantity": 1}',
        ]),

        # --- Dict ---
        ("dict --help", EnvCmd, ["--help"]),
        ("dict JSON", EnvCmd, [
            "--name", "job1",
            "--environment", '{"JAVA_HOME": "/usr/lib/jvm", "PATH": "/usr/bin"}'
        ]),
        ("dict key=value", EnvCmd, [
            "--name", "job1",
            "--environment", "JAVA_HOME=/usr/lib/jvm",
            "--environment", "PATH=/usr/bin",
        ]),
        ("dict + labels", EnvCmd, [
            "--name", "job1",
            "--environment", '{"K": "V"}',
            "--labels", "team=backend",
            "--labels", "env=prod",
        ]),

        # --- Enum ---
        ("enum --help", EnumCmd, ["--help"]),
        ("enum default", EnumCmd, ["--name", "John"]),
        ("enum explicit", EnumCmd, ["--name", "John", "--role", "admin"]),
        ("enum invalid", EnumCmd, ["--name", "John", "--role", "superadmin"]),

        # --- Mixed ---
        ("mixed --help", ComplexCmd, ["--help"]),
        ("mixed all", ComplexCmd, [
            "--name", "John",
            "--role", "admin",
            "--tags", "dev", "--tags", "lead",
            "--address.city", "NYC",
            "--metadata", "team=backend",
        ]),
    ]

    for desc, model, args in tests:
        print(f"\n--- {desc} ---")
        print(f"  args: {' '.join(args)}")
        try:
            CliApp.run(model, cli_args=args)
            print("  [OK]")
        except SystemExit as e:
            if e.code == 0:
                print("  [EXIT 0 - help]")
            else:
                print(f"  [EXIT {e.code}]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
