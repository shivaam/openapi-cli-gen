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

## Quick Start

```bash
pip install openapi-cli-gen
```

### Generate a CLI Package

```bash
openapi-cli-gen generate --spec https://api.example.com/openapi.json --name mycli
cd mycli && pip install -e .
mycli users list
mycli users create --name John --email john@example.com --address.city NYC
```

### Run Instantly (No Code Generation)

```bash
openapi-cli-gen run --spec api.yaml users list --limit 10
```

### Inspect a Spec

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

## Tested Against Real APIs

We don't just test against toy specs. Here's what works today.

### Apache Airflow (111 endpoints, 139 schemas)

Live tested against Airflow 3.2.0. Full CRUD — create, read, update, delete — all validated:

```bash
# Create a connection with nested fields
airflow Connection post --connection-id my-db --conn-type postgres --host db.example.com --port 5432

# Update it
airflow Connection patch --connection-id my-db --conn-type postgres --host new-host.example.com

# Trigger a DAG run with datetime params
airflow DagRun trigger-dag-run --dag-id my_dag --logical-date 2026-04-09T12:00:00+00:00

# Create resources
airflow Pool post --name my-pool --slots 10 --description "Created via CLI"
airflow Variable post --key my-var --value hello-world

# List and query
airflow DAG get-dags --limit 5
airflow Provider get
airflow Monitor get-health

# Clean up
airflow Connection delete --connection-id my-db
```

| Method | Endpoints tested | Result |
|---|---|---|
| GET | 19 | All pass |
| POST | 4 | All pass |
| PATCH | 1 | Pass |
| DELETE | 3 | All pass |

### Swagger Petstore (19 endpoints)

```bash
openapi-cli-gen inspect --spec https://petstore3.swagger.io/api/v3/openapi.json
# → 19 endpoints, 3 groups (pet, store, user), 2 auth schemes
```

### Open-Meteo Weather API

```bash
openapi-cli-gen inspect --spec https://raw.githubusercontent.com/open-meteo/open-meteo/main/openapi.yml
```

## The Core Feature: Nested Model Flattening

This is what no other tool does. Your API has nested request bodies — we flatten them into CLI flags at any depth:

```bash
# Depth 1: address nested inside user
mycli users create --name John --address.city NYC --address.state NY

# Depth 2: CEO nested inside company
mycli companies create --name Acme --ceo.name Bob --ceo.email bob@acme.com

# Depth 3: backoff config inside retry inside job
mycli jobs create --name etl --retry.backoff.strategy exponential --retry.backoff.initial-delay-ms 2000

# JSON fallback when you need it
mycli users create --address '{"street": "123 Main", "city": "NYC"}'

# Mix both — dot-notation wins
mycli users create --address '{"city": "NYC"}' --address.city SF  # city=SF
```

### Arrays, Dicts, Enums

```bash
# Arrays: repeated flags, comma-separated, or JSON
mycli users create --tags admin --tags reviewer
mycli users create --tags admin,reviewer
mycli orders create --items '[{"product_id": "abc", "quantity": 2}]'

# Dicts: key=value or JSON
mycli jobs create --environment JAVA_HOME=/usr/lib/jvm
mycli jobs create --environment '{"JAVA_HOME": "/usr/lib/jvm"}'

# Enums: validated choices shown in --help
mycli users create --role admin   # {admin, user, viewer}
```

## Authentication

Auto-configures from your spec's `securitySchemes`:

```bash
# Environment variable (recommended for CI/CD)
export MYCLI_TOKEN=sk-xxx
mycli users list

# Flag (overrides env var)
mycli users list --token sk-xxx
```

| Spec scheme | CLI flag | Env var |
|---|---|---|
| Bearer token | `--token` | `{NAME}_TOKEN` |
| API key | `--api-key` | `{NAME}_API_KEY` |
| Basic auth | `--username`, `--password` | `{NAME}_USERNAME`, `{NAME}_PASSWORD` |

## As a Library

### New CLI from a spec

```python
from openapi_cli_gen import build_cli

app = build_cli(spec="openapi.yaml", name="mycli")
app()
```

### Plug into your existing CLI

Already have a CLI with custom commands? Add auto-generated API commands alongside them:

```python
from openapi_cli_gen import build_command_group

registry = build_command_group(spec="openapi.yaml", name="mycli")
# Returns {group: {command: CommandInfo}} — integrate with your existing argparse CLI
```

## How It Works

```
Your OpenAPI spec (YAML/JSON)
    |
    v
1. Load & resolve all $ref references (jsonref)
2. Generate typed Pydantic models (datamodel-code-generator, cached)
3. Group endpoints by tag -> command groups
4. Flatten request body schemas into CLI flags (pydantic-settings)
5. Build CLI: mycli <group> <command> --flags
    |
    v
Working CLI — first run ~300ms, cached ~50ms
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

## Why This Exists

Every CLI framework (Click, Typer, argparse) makes you define flags manually. Every OpenAPI code generator (openapi-python-client, openapi-generator) produces HTTP client libraries, not CLIs. Nobody bridged the gap — taking nested API schemas and turning them into ergonomic `--flag` arguments.

We do.

- **For API providers**: ship a CLI for your users in minutes, not weeks
- **For developers**: instant CLI access to any API with an OpenAPI spec
- **For platform teams**: generate CLIs for 30 microservices without writing 30 CLI wrappers

## Supported

- OpenAPI 3.0 and 3.1
- All HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Local, external, and circular `$ref` resolution
- Path parameters, query parameters, request bodies
- Nested objects at any depth, arrays, dicts, enums, nullable fields
- Bearer token and API key authentication
- JSON, YAML, table, and raw output formats
- 50 automated tests + live API validation

## Status

Early release (v0.0.1). Core features work. Roadmap includes Typer output target (rich `--help`, shell completion), auto-pagination, OAuth2, and more.

[Issues and feedback welcome.](https://github.com/shivaam/openapi-cli-gen/issues)

## License

MIT
