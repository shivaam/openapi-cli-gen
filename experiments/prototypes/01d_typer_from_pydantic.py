"""
Experiment 1d: Dynamically generate Typer commands from Pydantic models.

Walk model fields → create typer.Option() for each → register as command.
Get Typer UX (rich --help, completion) with zero manual per-command code.
"""

import time
import inspect
from typing import Any, get_args, get_origin

import typer
from pydantic import BaseModel
from pydantic.fields import FieldInfo


# ============================
# Models (same as other experiments)
# ============================

class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UsersCreateCmd(BaseModel):
    """Create a new user."""
    name: str
    email: str
    age: int = 25
    role: str = "user"
    address: Address | None = None
    tags: list[str] | None = None


class UsersListCmd(BaseModel):
    """List all users."""
    limit: int = 20
    offset: int = 0
    role: str | None = None


class UsersGetCmd(BaseModel):
    """Get a user by ID."""
    user_id: str


class OrdersListCmd(BaseModel):
    """List all orders."""
    status: str | None = None
    customer_id: str | None = None


class OrdersCreateCmd(BaseModel):
    """Create an order."""
    customer_id: str
    notes: str | None = None


class TagsCreateCmd(BaseModel):
    """Create a tag."""
    name: str


class JobsCreateCmd(BaseModel):
    """Create a job."""
    name: str
    parallelism: int = 1


# ============================
# The magic: model → Typer command, dynamically
# ============================

def _is_pydantic_model(annotation) -> bool:
    """Check if a type annotation is a Pydantic BaseModel subclass."""
    try:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except TypeError:
        return False


def _unwrap_optional(annotation):
    """Unwrap Optional[X] / X | None → X."""
    origin = get_origin(annotation)
    if origin is type(int | str):  # UnionType
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0], True
        return annotation, False
    return annotation, False


def _collect_fields(model: type[BaseModel], prefix: str = "") -> list[dict]:
    """Recursively collect fields from a Pydantic model, flattening nested models."""
    fields = []
    for field_name, field_info in model.model_fields.items():
        full_name = f"{prefix}{field_name}" if not prefix else f"{prefix}.{field_name}"
        flag_name = f"--{full_name.replace('_', '-')}"

        annotation = field_info.annotation
        unwrapped, is_optional = _unwrap_optional(annotation)

        if _is_pydantic_model(unwrapped):
            # Recurse into nested model
            nested_fields = _collect_fields(unwrapped, prefix=full_name)
            fields.extend(nested_fields)
        else:
            # Leaf field — create a CLI option
            python_type = unwrapped
            # Handle list[str] etc
            origin = get_origin(unwrapped)
            if origin is list:
                python_type = list[get_args(unwrapped)[0]] if get_args(unwrapped) else list[str]

            default = field_info.default
            required = default is ... or (field_info.is_required() and not is_optional)
            if is_optional and default is ...:
                default = None
                required = False

            fields.append({
                "name": full_name,
                "flag": flag_name,
                "type": python_type,
                "default": default if not required else ...,
                "required": required,
                "description": field_info.description or "",
                "is_optional": is_optional,
            })

    return fields


def make_typer_command(
    model: type[BaseModel],
    callback: callable,
) -> callable:
    """Create a Typer-compatible function from a Pydantic model.

    Returns a function with proper type annotations that Typer can introspect.
    """
    fields = _collect_fields(model)

    # Build parameter names (sanitized for Python)
    param_names = {}
    for f in fields:
        param_name = f["name"].replace(".", "__").replace("-", "_")
        param_names[f["name"]] = param_name

    def command_func(**kwargs):
        # Reconstruct the nested model from flat kwargs
        data = {}
        for f in fields:
            param_name = param_names[f["name"]]
            value = kwargs.get(param_name)
            if value is None:
                continue

            # Handle nested: "address.city" → data["address"]["city"]
            parts = f["name"].split(".")
            target = data
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value

        instance = model.model_validate(data)
        callback(instance)

    # Dynamically set the function's annotations and defaults for Typer
    annotations = {}
    defaults = {}
    for f in fields:
        param_name = param_names[f["name"]]

        # Map types to Typer-compatible types
        py_type = f["type"]
        origin = get_origin(py_type)
        if origin is list:
            inner = get_args(py_type)
            py_type = list[inner[0]] if inner else list[str]

        if f["required"]:
            annotations[param_name] = py_type
            defaults[param_name] = typer.Option(..., f["flag"], help=f["description"] or f["name"])
        elif f["is_optional"]:
            annotations[param_name] = py_type | None
            default_val = f["default"] if f["default"] is not ... else None
            defaults[param_name] = typer.Option(default_val, f["flag"], help=f["description"] or f["name"])
        else:
            annotations[param_name] = py_type
            defaults[param_name] = typer.Option(f["default"], f["flag"], help=f["description"] or f["name"])

    command_func.__annotations__ = annotations
    command_func.__doc__ = model.__doc__

    # Set defaults on the function
    import types
    params = []
    for param_name in annotations:
        params.append(inspect.Parameter(
            param_name,
            inspect.Parameter.KEYWORD_ONLY,
            default=defaults[param_name],
            annotation=annotations[param_name],
        ))
    command_func.__signature__ = inspect.Signature(params)

    return command_func


def register_commands(
    app: typer.Typer,
    group_name: str,
    commands: dict[str, type[BaseModel]],
    group_help: str = "",
):
    """Register a group of Pydantic model-based commands on a Typer app."""
    group = typer.Typer(help=group_help)

    for cmd_name, model in commands.items():
        def make_callback(m):
            def cb(instance):
                print(f"{cmd_name}: {instance.model_dump_json(indent=2)}")
            return cb

        func = make_typer_command(model, make_callback(model))
        group.command(cmd_name)(func)

    app.add_typer(group, name=group_name)


# ============================
# Build the CLI from registry
# ============================

COMMAND_REGISTRY = {
    "users": {
        "help": "User management",
        "commands": {
            "list": UsersListCmd,
            "create": UsersCreateCmd,
            "get": UsersGetCmd,
        },
    },
    "orders": {
        "help": "Order management",
        "commands": {
            "list": OrdersListCmd,
            "create": OrdersCreateCmd,
        },
    },
    "tags": {
        "help": "Tag management",
        "commands": {
            "create": TagsCreateCmd,
        },
    },
    "jobs": {
        "help": "Job management",
        "commands": {
            "create": JobsCreateCmd,
        },
    },
}


def build_app() -> typer.Typer:
    app = typer.Typer(help="Auto-generated CLI from Pydantic models")
    for group_name, group_config in COMMAND_REGISTRY.items():
        register_commands(
            app,
            group_name,
            group_config["commands"],
            group_help=group_config["help"],
        )
    return app


# ============================
# Test
# ============================

if __name__ == "__main__":
    from typer.testing import CliRunner

    app = build_app()
    runner = CliRunner()

    print("=" * 60)
    print("EXPERIMENT 1d: Typer from Pydantic (dynamic)")
    print("=" * 60)

    test_cases = [
        ("Root --help", ["--help"]),
        ("users --help", ["users", "--help"]),
        ("users create --help", ["users", "create", "--help"]),
        ("users list", ["users", "list", "--limit", "10"]),
        ("users create flat", ["users", "create", "--name", "John", "--email", "j@x.com"]),
        ("users create nested", ["users", "create", "--name", "John", "--email", "j@x.com", "--address.city", "NYC"]),
        ("users get", ["users", "get", "--user-id", "abc-123"]),
        ("orders list", ["orders", "list", "--status", "pending"]),
        ("orders create", ["orders", "create", "--customer-id", "cust-1"]),
        ("tags create", ["tags", "create", "--name", "admin"]),
        ("jobs create", ["jobs", "create", "--name", "etl", "--parallelism", "4"]),
    ]

    for desc, args in test_cases:
        print(f"\n--- {desc}: mycli {' '.join(args)} ---")
        result = runner.invoke(app, args)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        if result.exception and not isinstance(result.exception, SystemExit):
            print(f"  [ERROR] {type(result.exception).__name__}: {result.exception}")
        elif result.exit_code != 0:
            print(f"  [EXIT {result.exit_code}]")
        else:
            print("  [OK]")

    # Benchmark
    print(f"\n--- Benchmark ---")
    app2 = build_app()
    start = time.perf_counter()
    for _ in range(100):
        runner.invoke(app2, ["users", "list", "--limit", "5"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 flat runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")

    start = time.perf_counter()
    for _ in range(100):
        runner.invoke(app2, ["users", "create", "--name", "J", "--email", "j@x", "--address.city", "NYC"])
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 nested runs: {elapsed:.1f}ms total, {elapsed/100:.1f}ms avg")
