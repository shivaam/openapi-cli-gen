# Architecture References from Similar Tools

## Patterns to Adopt

### From openapi-python-client (1.9k stars)
**5-stage pipeline**: CLI → Load spec → Validate → Parse to IR → Generate via Jinja2

Key patterns:
- **Vendored Pydantic schema models** for parsing OpenAPI (33 files, one per object type)
- **Property type system** — 15 concrete types, each with own Jinja2 template
- **Multi-round processing** — loops until no more progress for forward references
- **Custom template override** — Jinja2 ChoiceLoader (user templates > built-in defaults)
- **Union return types** — `Endpoint | ParseError` instead of exceptions, allows partial generation
- **Config via Pydantic model** — `ConfigFile` with overrides, naming, post-hooks

### From datamodel-code-generator (3.9k stars)
**10-stage pipeline**: Config → Detect type → Select backend → Create parser → Walk schema → Post-process → Render → Collect imports → Format → Output

Key patterns:
- **Parser inheritance**: `Parser(ABC)` → `JsonSchemaParser` → `OpenAPIParser`
- **DataModelSet** — NamedTuple bundling all backend-specific types (model, field, type manager)
- **ModelResolver** — central registry for $ref tracking and name deduplication
- **Tarjan's SCC** — circular dependency detection via graph algorithms
- **Topological sort** — stable ordering for model output
- **130+ config fields** in a single GenerateConfig Pydantic model
- **Multiple output backends**: Pydantic v2, dataclass, TypedDict, msgspec — same IR, different templates

### From Airflow's airflowctl (production)
**Runtime introspection pipeline**: OpenAPI → datamodel-codegen → operations.py → AST parse → CommandFactory → argparse

Key patterns:
- **CommandFactory** — single class orchestrating the entire CLI generation (987 lines)
- **AST introspection** — parses operations.py without importing it
- **Universal handler** — one `_get_func()` handles ALL generated commands via functools.partial
- **Two-phase reconstruction** — CLI flags → flat dict → Pydantic model via model_validate()
- **Decorator pattern** — `@provide_api_client` injects authenticated client
- **Property pattern** — `Client.dags`, `Client.pools` with @lru_cache

### From specli (our closest competitors — BOTH are runtime-only)
**Vercel npm specli** (115 stars, TypeScript):
- Runtime Commander.js CLI from spec
- Dot-notation for nested objects in body flags
- **Skips arrays entirely** ("Skip arrays and other complex types for now")
- AI/agent-focused (Vercel AI SDK tool wrapper)
- Stalled 2.5 months

**PyPI specli** (1 star, Python):
- Runtime Typer CLI from spec
- Complex types → JSON strings
- Plugin system for auth (10 plugins)
- 49 downloads/month, stalled 6 weeks

## Our Differentiators vs All Competitors

1. **Code generation** — we emit real Python files, not runtime interpretation
2. **Pydantic model flattening** — nested models become typed --flags, not JSON strings
3. **Two modes** — codegen (primary) + runtime (convenience)
4. **pydantic-settings integration** — CLI + env vars + config files with priority chain
5. **Readable, editable output** — providers own and customize the generated code

## Recommended Architecture for openapi-cli-gen

```
src/openapi_cli_gen/
├── cli.py                    # Our CLI entry point (Typer)
├── config.py                 # GenerateConfig Pydantic model
├── spec/                     # OpenAPI spec handling
│   ├── loader.py             # Load from file/URL, detect 3.0 vs 3.1
│   ├── resolver.py           # $ref resolution
│   └── parser.py             # Parse endpoints, group by tag, extract params
├── models/                   # Model generation layer
│   └── generator.py          # Wraps datamodel-code-generator
├── commands/                 # CLI command generation
│   ├── builder.py            # Map endpoints → CLI commands
│   └── flattener.py          # Nested model → flat flags logic
├── codegen/                  # Code output (Jinja2)
│   ├── emitter.py            # Orchestrates file generation
│   └── templates/            # Jinja2 templates
│       ├── cli.py.jinja2
│       ├── commands.py.jinja2
│       ├── client.py.jinja2
│       └── pyproject.toml.jinja2
├── runtime/                  # Runtime mode (run without codegen)
│   └── runner.py             # Build CLI in-memory, execute
└── output/                   # Output formatting
    └── formatter.py          # JSON, table, YAML output
```

### Key Design Principle
Separate the **core engine** (spec parsing, model gen, endpoint mapping, flattening) from the **output targets** (codegen templates, runtime runner). This lets us add Typer output, Click output, or any future framework without touching the core.
