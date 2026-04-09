"""
Experiment 13: Does create_model() with nested BaseModel fields work with CliApp?

This is critical: we need to dynamically create Pydantic models from
parsed schemas AND have them work with pydantic-settings CLI flattening.
"""

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_settings import CliApp


# === Approach A: Pre-defined models (control — should always work) ===

class Address(BaseModel):
    city: str | None = None
    state: str | None = None


class StaticUser(BaseModel):
    """Statically defined user with nested address."""
    name: str
    email: str
    address: Address | None = None

    def cli_cmd(self):
        print(f"Static: {self.model_dump_json(indent=2)}")


# === Approach B: Dynamic model with pre-defined nested type ===

DynamicUserWithStatic = create_model(
    "DynamicUserWithStatic",
    __doc__="Dynamic user, static Address.",
    name=(str, FieldInfo()),
    email=(str, FieldInfo()),
    address=(Address | None, FieldInfo(default=None)),
)


# === Approach C: Fully dynamic — nested model also created with create_model ===

DynamicAddress = create_model(
    "DynamicAddress",
    city=(str | None, FieldInfo(default=None)),
    state=(str | None, FieldInfo(default=None)),
)

DynamicUserFull = create_model(
    "DynamicUserFull",
    __doc__="Fully dynamic user with dynamic address.",
    name=(str, FieldInfo()),
    email=(str, FieldInfo()),
    address=(DynamicAddress | None, FieldInfo(default=None)),
)


# === Approach D: 3-level dynamic nesting ===

DynamicBackoff = create_model(
    "DynamicBackoff",
    strategy=(str, FieldInfo(default="linear")),
    initial_delay_ms=(int, FieldInfo(default=1000)),
)

DynamicRetry = create_model(
    "DynamicRetry",
    max_attempts=(int, FieldInfo(default=3)),
    backoff=(DynamicBackoff | None, FieldInfo(default=None)),
)

DynamicJob = create_model(
    "DynamicJob",
    __doc__="Fully dynamic 3-level nesting.",
    name=(str, FieldInfo()),
    parallelism=(int, FieldInfo(default=1)),
    retry=(DynamicRetry | None, FieldInfo(default=None)),
)


# === Approach E: Dynamic model with list and dict ===

DynamicComplex = create_model(
    "DynamicComplex",
    __doc__="Dynamic with list and dict.",
    name=(str, FieldInfo()),
    tags=(list[str] | None, FieldInfo(default=None)),
    metadata=(dict[str, str] | None, FieldInfo(default=None)),
    address=(DynamicAddress | None, FieldInfo(default=None)),
)


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 13: Dynamic Nested Models + CliApp")
    print("=" * 60)

    tests = [
        # Static control
        ("Static --help", StaticUser, ["--help"]),
        ("Static nested", StaticUser, ["--name", "John", "--email", "j@x", "--address.city", "NYC"]),

        # Dynamic with static nested
        ("DynStatic --help", DynamicUserWithStatic, ["--help"]),
        ("DynStatic nested", DynamicUserWithStatic, ["--name", "John", "--email", "j@x", "--address.city", "NYC"]),

        # Fully dynamic
        ("FullDynamic --help", DynamicUserFull, ["--help"]),
        ("FullDynamic nested", DynamicUserFull, ["--name", "John", "--email", "j@x", "--address.city", "NYC"]),

        # 3-level dynamic
        ("3-level --help", DynamicJob, ["--help"]),
        ("3-level nested", DynamicJob, [
            "--name", "etl",
            "--retry.max-attempts", "5",
            "--retry.backoff.strategy", "exponential",
        ]),

        # Dynamic with list + dict
        ("Complex --help", DynamicComplex, ["--help"]),
        ("Complex all", DynamicComplex, [
            "--name", "test",
            "--tags", "a", "--tags", "b",
            "--metadata", "k=v",
            "--address.city", "NYC",
        ]),
    ]

    for desc, model, args in tests:
        print(f"\n--- {desc} ---")
        print(f"  args: {' '.join(args)}")

        # Add cli_cmd if missing
        if not hasattr(model, "cli_cmd"):
            def make_cmd(m):
                def cli_cmd(self):
                    print(f"  Result: {self.model_dump_json(indent=2)}")
                return cli_cmd
            model.cli_cmd = make_cmd(model)

        try:
            CliApp.run(model, cli_args=args)
            print("  [OK]")
        except SystemExit as e:
            print(f"  [EXIT {e.code}]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
