from pydantic import BaseModel
from pydantic_settings import CliApp
from openapi_cli_gen.engine.models import schema_to_model


def test_flat_model():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 25},
        },
    }
    Model = schema_to_model("TestFlat", schema)
    assert issubclass(Model, BaseModel)
    instance = Model(name="John")
    assert instance.name == "John"
    assert instance.age == 25


def test_nested_model():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                },
            },
        },
    }
    Model = schema_to_model("TestNested", schema)
    instance = Model(name="John", address={"city": "NYC"})
    assert instance.address.city == "NYC"


def test_array_of_primitives():
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    Model = schema_to_model("TestArray", schema)
    instance = Model(tags=["a", "b"])
    assert instance.tags == ["a", "b"]


def test_nullable_field():
    schema = {
        "type": "object",
        "properties": {
            "value": {"type": ["string", "null"]},
        },
    }
    Model = schema_to_model("TestNullable", schema)
    instance = Model(value=None)
    assert instance.value is None


def test_enum_field():
    schema = {
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["admin", "user"], "default": "user"},
        },
    }
    Model = schema_to_model("TestEnum", schema)
    instance = Model()
    assert instance.role == "user"


def test_dict_field():
    schema = {
        "type": "object",
        "properties": {
            "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
        },
    }
    Model = schema_to_model("TestDict", schema)
    instance = Model(metadata={"k": "v"})
    assert instance.metadata == {"k": "v"}


def test_model_works_with_cliapp():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 25},
        },
    }
    Model = schema_to_model("TestCli", schema)
    Model.cli_cmd = lambda self: None
    CliApp.run(Model, cli_args=["--name", "John", "--age", "30"])


def test_nested_model_works_with_cliapp():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
            },
        },
    }
    Model = schema_to_model("TestNestedCli", schema)
    Model.cli_cmd = lambda self: None
    CliApp.run(Model, cli_args=["--name", "John", "--address.city", "NYC"])
