# Competitive Landscape

## Direct Competitors (OpenAPI → CLI)

| Tool | Language | Stars | Status | Generates Code? | Flattens Bodies? |
|------|----------|-------|--------|----------------|-----------------|
| Stainless CLI | Go | Commercial | Active | Yes (Go binary) | Yes (2-level dot notation) |
| restish | Go | 1,300 | Active | No (runtime) | No (JSON stdin) |
| openapi-to-cli (ocli) | TypeScript | 193 | Active | No (runtime) | No |
| specli (Vercel Labs) | Python | 115 | Active | Yes (Typer) | Unknown depth |
| openapi-cli-generator | Go | 208 | DEAD (2020) | Yes (Go) | No |
| openapi-cli-generator | Python | 1 | DEAD (2024) | No (runtime) | No (--data JSON) |
| mcp2cli | Python | 1,890 | Active | No (runtime) | No |

## Adjacent Tools (SDK Generators, not CLI)

| Tool | Language | Stars | What it does |
|------|----------|-------|-------------|
| openapi-python-client | Python | 1,932 | OpenAPI → Python HTTP client (attrs-based) |
| openapi-generator | Java/Multi | 26,074 | OpenAPI → SDK in 40+ languages |
| Fern | TypeScript | 3,580 | OpenAPI → SDK (commercial focus) |
| Speakeasy | Commercial | N/A | OpenAPI → SDK (commercial) |

## Pydantic → CLI Bridge Libraries

| Tool | Stars | Nested Models? | Lists of Objects? | Unions? |
|------|-------|---------------|-------------------|---------|
| pydantic-settings CLI | 1,302 | Yes (dot notation) | Partial | CliSubCommand |
| pydanclick | 59 | Yes (dash-joined) | Experimental | JSON only |
| pydantic-typer | 36 | Yes (dot notation) | No | No |
| tyro | 1,016 | Yes (dot notation) | Yes | Auto-subcommands |
| cyclopts | 1,116 | Yes (dot notation) | Basic | Left-to-right |
| clipstick | 42 | Basic | Unknown | Unknown |
| pydantic-cli | 160 | NO (flat only) | List[T] only | No |

## Our Unique Position

No existing tool combines:
1. OpenAPI spec input (broadest reach)
2. Python code generation (not runtime)
3. Pydantic model flattening into CLI flags
4. pydantic-settings multi-source config (CLI + env + files)
5. Distributable CLI package output

Closest gap: Stainless does 1+3+5 but is Go-only, commercial, closed-source.
