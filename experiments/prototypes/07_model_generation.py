"""
Experiment 7: Can we call datamodel-code-generator programmatically?
"""

import time
from pathlib import Path


def test_basic_generation():
    """Generate Pydantic models from our test spec."""
    print("\n--- Basic model generation ---")

    from datamodel_code_generator import generate, InputFileType, DataModelType

    spec_path = Path(__file__).parent.parent / "server" / "spec.yaml"

    start = time.perf_counter()
    result = generate(
        input_=spec_path,
        input_file_type=InputFileType.OpenAPI,
        output_model_type=DataModelType.PydanticV2BaseModel,
        use_annotated=True,
        field_constraints=True,
        snake_case_field=True,
        use_schema_description=True,
        use_field_description=True,
    )
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Generated in {elapsed:.1f}ms")
    print(f"  Output length: {len(result)} chars")
    print(f"  Lines: {result.count(chr(10))}")

    # Show first 80 lines
    lines = result.split("\n")
    print(f"\n  === First 80 lines ===")
    for i, line in enumerate(lines[:80]):
        print(f"  {i+1:4}: {line}")

    if len(lines) > 80:
        print(f"  ... ({len(lines) - 80} more lines)")

    return result


def test_base_settings():
    """Generate with BaseSettings as base class."""
    print("\n--- BaseSettings base class ---")

    from datamodel_code_generator import generate, InputFileType, DataModelType

    spec_path = Path(__file__).parent.parent / "server" / "spec.yaml"

    try:
        result = generate(
            input_=spec_path,
            input_file_type=InputFileType.OpenAPI,
            output_model_type=DataModelType.PydanticV2BaseModel,
            base_class="pydantic_settings.BaseSettings",
            additional_imports=["pydantic_settings.BaseSettings"],
            use_annotated=True,
            field_constraints=True,
        )
        print(f"  Output length: {len(result)} chars")
        # Check if BaseSettings is in the output
        if "BaseSettings" in result:
            print("  [OK] BaseSettings in output")
        else:
            print("  [WARN] BaseSettings NOT in output")

        # Show a model sample
        lines = result.split("\n")
        in_model = False
        for line in lines:
            if "class UserCreate" in line:
                in_model = True
            if in_model:
                print(f"  {line}")
                if line.strip() == "" and in_model:
                    break
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def test_specific_schemas_only():
    """Can we generate models for only specific schemas?"""
    print("\n--- Specific schemas only ---")

    from datamodel_code_generator import generate, InputFileType, DataModelType
    import yaml

    spec_path = Path(__file__).parent.parent / "server" / "spec.yaml"
    raw = yaml.safe_load(spec_path.read_text())

    # Extract just the schemas we want
    subset = {
        "type": "object",
        "properties": {},
        "$defs": {
            "UserCreate": raw["components"]["schemas"]["UserCreate"],
            "Address": raw["components"]["schemas"]["Address"],
        },
    }

    try:
        result = generate(
            input_=str(subset),
            input_file_type=InputFileType.JsonSchema,
            output_model_type=DataModelType.PydanticV2BaseModel,
            use_annotated=True,
        )
        print(f"  Output length: {len(result)} chars")
        print(f"  Models generated:")
        for line in result.split("\n"):
            if line.startswith("class "):
                print(f"    {line}")
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def test_custom_class_names():
    """Test custom class name generator."""
    print("\n--- Custom class name generator ---")

    from datamodel_code_generator import generate, InputFileType, DataModelType

    spec_path = Path(__file__).parent.parent / "server" / "spec.yaml"

    def prefix_generator(name: str) -> str:
        return f"API{name}"

    try:
        result = generate(
            input_=spec_path,
            input_file_type=InputFileType.OpenAPI,
            output_model_type=DataModelType.PydanticV2BaseModel,
            custom_class_name_generator=prefix_generator,
        )
        print(f"  Classes generated:")
        for line in result.split("\n"):
            if line.startswith("class "):
                print(f"    {line}")
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 7: datamodel-code-generator Programmatic Usage")
    print("=" * 60)

    test_basic_generation()
    test_base_settings()
    test_specific_schemas_only()
    test_custom_class_names()
