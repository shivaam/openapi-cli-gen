# pydantic-settings CLI: Technical Deep Dive

## How It Works Internally

CliSettingsSource extends EnvSettingsSource — CLI args are treated as "env vars" with `.` as nested delimiter. Argparse does NO type conversion — all values are strings. Pydantic handles all validation during model construction.

## Nesting

- **No depth limit**: Tested at depth 50 (5ms parser creation)
- **Dot-notation always wins**: `--sub '{"x":1}' --sub.x 2` → x=2 regardless of order
- **cli_avoid_json=True**: Hides JSON args from --help but they still work
- **Recursive models**: Parser stops at first re-encounter of same class (prevents infinite loop). Deeper recursion requires JSON.

## List Handling (3 Intermixable Syntaxes)

```bash
# JSON
--tags '["a","b","c"]'

# Repeated flags
--tags a --tags b --tags c

# Comma-separated
--tags a,b,c

# Mixed (all work together)
--tags a --tags '["b","c"]'
```

**Lists of objects**: NO dot-notation into indices. Must use JSON:
```bash
--servers '{"host":"a"}' --servers '{"host":"b"}'
# There is NO --servers.0.host syntax
```
This is the biggest limitation for our use case.

## Discriminated Unions

Well-supported:
- ALL fields from ALL union members flattened into argparse group
- Discriminator field gets metavar `{variant1,variant2}`
- Common fields across members deduplicated
- Pydantic picks right variant based on discriminator value

## CliApp

```python
# Wraps any BaseModel (not just BaseSettings)
CliApp.run(MyModel)  # → creates temp BaseSettings subclass with good defaults:
# cli_avoid_json=True, cli_enforce_required=True, 
# cli_implicit_flags=True, cli_kebab_case=True

# Round-trip serialization
args = CliApp.serialize(model_instance)  # → list[str] of CLI args
CliApp.run(MyModel, cli_args=args)       # → reproduces original model
```

## Performance

| Operation | Time |
|-----------|------|
| 500 fields parser creation | 14ms |
| Depth 50 nesting | 5ms |
| Parsing 50 args | 0.2ms |

## Key Limitations

1. **list[SomeModel] requires JSON** — no --items.0.field syntax
2. **Recursive models stop at first re-encounter** — deeper needs JSON
3. **No shell completion** — unlike Typer/Click
4. **Subcommand naming inconsistency** — single type uses field name, union uses class names
5. **AliasPath creates dict-style args** — --database port=5433 instead of --database.port
6. **Enum serialization** — CliApp.serialize() may produce LogLevel.DEBUG instead of debug
