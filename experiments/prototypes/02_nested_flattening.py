"""
Experiment 2: How does pydantic-settings handle nested models at depth 1, 2, 3?

Tests: dot-notation, cli_avoid_json, mixing JSON + dot-notation, --help readability
"""

from pydantic import BaseModel
from pydantic_settings import CliApp


# === Depth 1: User with Address ===

class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UserCreate(BaseModel):
    """Create a user (depth 1 nesting: address)."""
    name: str
    email: str
    age: int = 25
    address: Address | None = None
    tags: list[str] | None = None

    def cli_cmd(self):
        print(f"UserCreate: {self.model_dump_json(indent=2)}")


# === Depth 2: Company with CEO and Address ===

class CEO(BaseModel):
    name: str | None = None
    email: str | None = None


class Company(BaseModel):
    """Create a company (depth 2 nesting: ceo.name, address.city)."""
    name: str
    website: str | None = None
    address: Address | None = None
    ceo: CEO | None = None

    def cli_cmd(self):
        print(f"Company: {self.model_dump_json(indent=2)}")


# === Depth 3: Job with Retry with Backoff ===

class BackoffConfig(BaseModel):
    strategy: str = "linear"
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff: BackoffConfig | None = None


class JobConfig(BaseModel):
    """Create a job (depth 3 nesting: retry.backoff.strategy)."""
    name: str
    parallelism: int = 1
    retry: RetryConfig | None = None
    environment: dict[str, str] | None = None

    def cli_cmd(self):
        print(f"JobConfig: {self.model_dump_json(indent=2)}")


# === Test runner ===

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 2: Nested Model Flattening")
    print("=" * 60)

    tests = [
        # Depth 1 tests
        ("Depth 1: --help", UserCreate, ["--help"]),
        ("Depth 1: flat only", UserCreate, ["--name", "John", "--email", "j@x.com"]),
        ("Depth 1: dot-notation", UserCreate, [
            "--name", "John", "--email", "j@x.com",
            "--address.city", "NYC", "--address.state", "NY"
        ]),
        ("Depth 1: address as JSON", UserCreate, [
            "--name", "John", "--email", "j@x.com",
            "--address", '{"city": "NYC", "state": "NY"}'
        ]),
        ("Depth 1: mix JSON + dot override", UserCreate, [
            "--name", "John", "--email", "j@x.com",
            "--address", '{"city": "NYC", "state": "NY"}',
            "--address.city", "SF"
        ]),

        # Depth 2 tests
        ("Depth 2: --help", Company, ["--help"]),
        ("Depth 2: dot-notation", Company, [
            "--name", "Acme",
            "--ceo.name", "Bob", "--ceo.email", "bob@acme.com",
            "--address.city", "NYC"
        ]),

        # Depth 3 tests
        ("Depth 3: --help", JobConfig, ["--help"]),
        ("Depth 3: all dot-notation", JobConfig, [
            "--name", "etl-job",
            "--retry.max-attempts", "5",
            "--retry.backoff.strategy", "exponential",
            "--retry.backoff.initial-delay-ms", "2000"
        ]),
        ("Depth 3: retry as JSON", JobConfig, [
            "--name", "etl-job",
            "--retry", '{"max_attempts": 5, "backoff": {"strategy": "exponential"}}'
        ]),
        ("Depth 3: env dict", JobConfig, [
            "--name", "etl-job",
            "--environment", '{"JAVA_HOME": "/usr/lib/jvm", "PATH": "/usr/bin"}'
        ]),
    ]

    for desc, model, args in tests:
        print(f"\n--- {desc} ---")
        print(f"  args: {' '.join(args)}")
        try:
            CliApp.run(model, cli_args=args)
            print("  [OK]")
        except SystemExit as e:
            print(f"  [EXIT {e.code}]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
