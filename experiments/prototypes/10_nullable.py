"""
Experiment 10: How do nullable fields work in pydantic-settings CLI?

Tests: Optional[str], type: ["string", "null"] (3.1 style), passing null
"""

from pydantic import BaseModel
from pydantic_settings import CliApp


class NullableCmd(BaseModel):
    """Test nullable fields."""
    required_field: str
    optional_with_default: str = "hello"
    optional_none: str | None = None
    nullable_int: int | None = None
    required_nullable: str | None  # required but can be null

    def cli_cmd(self):
        print(f"Result: {self.model_dump_json(indent=2)}")


class NullableNestedCmd(BaseModel):
    """Test nullable nested model."""
    name: str

    class Address(BaseModel):
        city: str
        state: str | None = None

    address: Address | None = None

    def cli_cmd(self):
        print(f"Result: {self.model_dump_json(indent=2)}")


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 10: Nullable Fields")
    print("=" * 60)

    tests = [
        ("--help", NullableCmd, ["--help"]),
        ("All provided", NullableCmd, [
            "--required-field", "hello",
            "--optional-with-default", "world",
            "--optional-none", "present",
            "--nullable-int", "42",
            "--required-nullable", "not-null",
        ]),
        ("Minimal (just required)", NullableCmd, [
            "--required-field", "hello",
            "--required-nullable", "something",
        ]),
        ("Pass null string", NullableCmd, [
            "--required-field", "hello",
            "--required-nullable", "null",
        ]),
        ("Omit optional", NullableCmd, [
            "--required-field", "hello",
            "--required-nullable", "x",
        ]),

        # Nested nullable
        ("Nested --help", NullableNestedCmd, ["--help"]),
        ("Nested with address", NullableNestedCmd, [
            "--name", "John",
            "--address.city", "NYC",
        ]),
        ("Nested without address", NullableNestedCmd, [
            "--name", "John",
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
