# Technical Stack & Building Blocks

## The Pipeline

```
OpenAPI spec (YAML/JSON)
    │
    ▼
┌─────────────────────────────┐
│  datamodel-code-generator   │  OpenAPI → Pydantic v2 models
│  (3.9k stars, v0.56.0)      │  Handles: $ref, allOf/oneOf/anyOf, 
│                             │  recursive schemas, enums, naming
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  openapi-cli-gen            │  OUR CODE: the glue layer
│  - Parse endpoints/tags     │  - Map endpoints → command groups
│  - Configure model gen      │  - Generate CLI app structure
│  - Wire up auth             │  - Add HTTP client calls
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  pydantic-settings v2 CLI   │  Pydantic models → CLI flags
│  (1.3k stars)               │  Handles: dot-notation flattening,
│                             │  lists, env vars, config files
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  httpx                      │  Async HTTP client
│  (13k stars)                │  For making the actual API calls
└─────────────────────────────┘
```

## Tool Details

### datamodel-code-generator
- **What**: Generates Pydantic v2 models from OpenAPI/JSON Schema
- **Why use it**: 1,764 commits solving $ref resolution, schema composition, naming collisions. Reimplementing = weeks of inferior work.
- **Programmatic API**: `generate(schema, output_model_type=..., base_class=..., use_annotated=True)`
- **Key feature**: `--base-class pydantic_settings.BaseSettings` makes generated models CLI-ready
- **Customizable**: Jinja2 templates, class name generators, type overrides
- **Handles**: $ref, allOf (inheritance), oneOf (unions), anyOf (nullable), recursive schemas, enums

### pydantic-settings v2 CLI
- **What**: Turns Pydantic models into CLI tools with argparse
- **Why use it**: Built-in dot-notation flattening, 3 list syntaxes, CliSubCommand for unions
- **Key features**:
  - `cli_avoid_json=True` — never require JSON input
  - `cli_kebab_case=True` — --my-field instead of --my_field
  - `cli_shortcuts` — aliases like -v for --verbose
  - `CliApp.run()` — wraps any BaseModel into CLI-ready BaseSettings
  - Source priority: CLI > env vars > .env > config files (free!)
- **Limitations**: No shell completion, boolean flag UX issues, nested model edge cases

### httpx
- **What**: Modern async HTTP client for Python
- **Why**: Async-capable, connection pooling, timeout config, auth hooks

### Typer (potential — for generated CLI structure)
- **What**: CLI framework by FastAPI author, builds on Click
- **Why consider**: 19k stars, excellent --help generation, shell completion
- **Trade-off**: No native Pydantic support. Would need to generate Typer code directly rather than using pydantic-settings CLI. More work but better UX.

## Design Decisions to Make

### Runtime vs Code Generation
- **Runtime** (like restish): User installs our tool, points at a spec, gets CLI dynamically
- **Code generation** (like Stainless): User runs our tool once, gets a complete Python package
- **Recommendation**: Code generation. Users want distributable CLIs, not a dependency.

### pydantic-settings CLI vs Typer as CLI layer
- **pydantic-settings**: Less work, native Pydantic flattening, but no shell completion, basic --help
- **Typer**: More work to generate, but better UX (rich help, completion, colors)
- **Hybrid option**: Generate Typer commands but use pydantic-settings for model flattening logic

### Nesting strategy (following Stainless)
- Depth 0-2: Flatten into --flags with dot-notation
- Depth 3+: Fall back to --field-json / --field-file
- Arrays of primitives: Repeated flags (--tag a --tag b)
- Arrays of objects: JSON/YAML input
- Discriminated unions: JSON fallback (they're rare in practice)

## Real-World API Patterns (What We Must Handle)

| Pattern | Frequency | Example |
|---------|-----------|---------|
| Nullable fields | Everywhere (322 in Airflow, 2579 in Stripe) | `anyOf: [{type: string}, {type: "null"}]` |
| $ref to shared schemas | Dominant composition pattern | `$ref: "#/components/schemas/Pet"` |
| Enums | Common (9 named enums in Airflow) | `enum: ["queued", "running", "success"]` |
| Shallow nesting (1-2 levels) | Very common | `{name: {first: str, last: str}}` |
| Arrays of primitives | Common | `tags: [str]` |
| Deep nesting (3+ levels) | Rare (Stripe edge case) | Fall back to JSON |
| allOf (inheritance) | Uncommon (2 in GitHub) | Class inheritance |
| oneOf (discriminated unions) | Rare (8 in GitHub, 0 discriminators) | JSON fallback |
| Arrays of objects | Moderate | JSON/YAML input |
| File uploads (multipart) | Rare per API, but important | --file @path |

## Auth Patterns (95% Coverage)

| Type | How to handle | Example APIs |
|------|--------------|-------------|
| Bearer token | `--token` or `API_TOKEN` env var | Airflow, Stripe |
| API key header | `--api-key` or env var, configurable header | Petstore |
| HTTP Basic | `--username` + `--password` or config | Stripe |
| OAuth2 client credentials | Built-in flow, token caching | Airflow |

Store in `~/.config/toolname/config.toml`. Provide `mycli configure` command.
