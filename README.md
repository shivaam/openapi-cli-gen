# openapi-cli-gen

**Generate a full CLI from any OpenAPI spec in seconds. Nested request bodies become flat `--flags` automatically.**

[![PyPI](https://img.shields.io/pypi/v/openapi-cli-gen)](https://pypi.org/project/openapi-cli-gen/)
[![Python](https://img.shields.io/pypi/pyversions/openapi-cli-gen)](https://pypi.org/project/openapi-cli-gen/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```bash
# Instead of this:
curl -X POST /api/users -d '{"name": "John", "address": {"city": "NYC", "state": "NY"}}'

# You get this:
mycli users create --name John --address.city NYC --address.state NY
```

No tool existed to take an OpenAPI spec and produce a typed Python CLI where nested request bodies are flattened into individual `--flag` arguments. Until now.

## Why openapi-cli-gen?

- **Zero boilerplate** -- point at a spec, get a working CLI
- **Nested model flattening** -- `--address.city NYC` not `--data '{"address":{"city":"NYC"}}'`
- **Works at any depth** -- 1, 2, 3+ levels of nesting with automatic dot-notation
- **Arrays, dicts, enums** -- all handled (`--tags dev --tags lead`, `--env KEY=val`, `--role {admin,user}`)
- **Auth from your spec** -- reads `securitySchemes`, wires up `--token` + env vars automatically
- **Two modes** -- generate a pip-installable package OR run instantly without code generation
- **Pluggable** -- use standalone or plug API commands into your existing CLI

## Quick Start

```bash
pip install openapi-cli-gen
```

### Generate a CLI Package

```bash
openapi-cli-gen generate --spec https://api.example.com/openapi.json --name mycli
cd mycli && pip install -e .
```

Now your users can:

```bash
mycli users list
mycli users create --name John --email john@example.com --address.city NYC
mycli jobs create --retry.backoff.strategy exponential --retry.backoff.initial-delay-ms 2000
```

### Run Instantly (No Code Generation)

Don't want to generate files? Point directly at any spec:

```bash
openapi-cli-gen run --spec api.yaml users list --limit 10
```

### Inspect a Spec

See what commands would be generated before committing:

```bash
$ openapi-cli-gen inspect --spec api.yaml

API: My API v1.0
Endpoints: 14
Groups: 6
Auth schemes: 2

  users:
    GET     /users                  List all users
    POST    /users                  Create a new user [body]
    GET     /users/{user_id}        Get a user by ID
  orders:
    POST    /orders                 Create an order [body]
  ...
```

## The Core Feature: Nested Model Flattening

This is what makes openapi-cli-gen different from every other tool. Your API has nested request bodies -- we flatten them into ergonomic CLI flags:

```bash
# Depth 1: address nested inside user
mycli users create --name John --address.city NYC --address.state NY

# Depth 2: CEO nested inside company
mycli companies create --name Acme --ceo.name Bob --ceo.email bob@acme.com

# Depth 3: backoff nested inside retry nested inside job config
mycli jobs create --name etl --retry.backoff.strategy exponential --retry.backoff.initial-delay-ms 2000

# JSON fallback for anything complex
mycli users create --address '{"street": "123 Main", "city": "NYC"}'

# Mix both -- dot-notation overrides JSON
mycli users create --address '{"city": "NYC"}' --address.city SF  # city=SF wins
```

### Arrays

```bash
# Repeated flags for primitives
mycli users create --tags admin --tags reviewer
# Or comma-separated
mycli users create --tags admin,reviewer
# Or JSON
mycli users create --tags '["admin", "reviewer"]'

# JSON for arrays of objects
mycli orders create --items '[{"product_id": "abc", "quantity": 2}]'
```

### Dicts

```bash
# Key=value syntax
mycli jobs create --environment JAVA_HOME=/usr/lib/jvm --environment PATH=/usr/bin
# Or JSON
mycli jobs create --environment '{"JAVA_HOME": "/usr/lib/jvm"}'
```

### Enums

```bash
mycli users create --role admin   # choices shown in --help: {admin, user, viewer}
mycli users create --role superadmin  # ValidationError: Input should be 'admin', 'user' or 'viewer'
```

## As a Library

### Build a full CLI from a spec

```python
from openapi_cli_gen import build_cli

app = build_cli(spec="openapi.yaml", name="mycli")
app()
```

### Plug API commands into your existing CLI

Already have a CLI with custom commands? Add auto-generated API commands alongside them:

```python
from openapi_cli_gen import build_command_group

# Returns {group: {command: CommandInfo}}
registry = build_command_group(spec="openapi.yaml", name="mycli")
# Integrate with your existing argparse-based CLI
```

## Authentication

Auth auto-configures from your spec's `securitySchemes`:

```bash
# Via environment variable (recommended for CI/CD)
export MYCLI_TOKEN=sk-xxx
mycli users list

# Via flag (overrides env var)
mycli users list --token sk-xxx
```

| Spec scheme | CLI flag | Env var |
|---|---|---|
| Bearer token | `--token` | `{NAME}_TOKEN` |
| API key | `--api-key` | `{NAME}_API_KEY` |
| Basic auth | `--username`, `--password` | `{NAME}_USERNAME`, `{NAME}_PASSWORD` |

## How It Works

```
Your OpenAPI spec (YAML/JSON)
    |
    v
1. Load & resolve all $ref references (jsonref)
2. Parse into typed models (openapi-pydantic)
3. Group endpoints by tag -> command groups
4. Flatten request body schemas into CLI flags (pydantic-settings)
5. Build CLI with dispatch: mycli <group> <command> --flags
    |
    v
Working CLI in seconds
```

## Compared to Alternatives

| Feature | openapi-cli-gen | specli | restish | Stainless |
|---|---|---|---|---|
| Language | Python | TypeScript | Go | Go |
| Generates distributable code | Yes | No | No | Yes |
| Runtime mode (no codegen) | Yes | Yes | Yes | No |
| Nested model flattening | All depths | Scalars only | No | 2 levels |
| Typed Pydantic models | Yes | No | No | N/A |
| Auth from spec | Yes | Partial | Manual | Yes |
| Pluggable into existing CLI | Yes | No | No | No |
| Open source | Yes | Yes | Yes | No |

## Supported

- OpenAPI 3.0 and 3.1
- All HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Local, external, and circular `$ref` resolution
- Path parameters, query parameters, request bodies
- Nested objects, arrays, dicts, enums, nullable fields
- Bearer token and API key authentication
- JSON, YAML, table (rich), and raw output formats

## Status

Early release (v0.0.1). Core features work. Roadmap includes Typer output target (rich `--help`, shell completion), auto-pagination, OAuth2, and more.

[Issues and feedback welcome.](https://github.com/shivaam/openapi-cli-gen/issues)

## License

MIT
