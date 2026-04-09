# openapi-cli-gen

Generate typed Python CLIs from OpenAPI specs with Pydantic model flattening into CLI flags.

**The problem:** You have a REST API with an OpenAPI spec. You want a CLI client. Today you either hand-write one or use `curl` with raw JSON blobs. No tool takes nested request body schemas and flattens them into ergonomic `--flag` arguments.

**The solution:** `openapi-cli-gen` reads your OpenAPI 3.0/3.1 spec and produces a CLI where nested request bodies become flat, typed CLI flags with dot-notation.

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

### Run Instantly (No Generation)

```bash
openapi-cli-gen run --spec api.yaml users list --limit 10
```

### Inspect a Spec

```bash
openapi-cli-gen inspect --spec api.yaml
```

## Nested Model Flattening

The core feature. Nested request bodies become flat CLI flags:

```bash
# Instead of:
curl -X POST /users -d '{"name": "John", "address": {"city": "NYC", "state": "NY"}}'

# You get:
mycli users create --name John --address.city NYC --address.state NY
```

Arrays, dicts, and enums all work:

```bash
# Repeated flags for arrays
mycli users create --tags admin --tags reviewer

# Key=value for dicts
mycli jobs create --environment JAVA_HOME=/usr/lib/jvm

# Enum choices with validation
mycli users create --role admin   # choices: admin, user, viewer

# JSON for complex nested objects
mycli orders create --items '[{"product_id": "abc", "quantity": 2}]'
```

## As a Library

### Build a full CLI from a spec

```python
from openapi_cli_gen import build_cli

app = build_cli(spec="openapi.yaml", name="mycli")
app()
```

### Plug API commands into an existing CLI

```python
from openapi_cli_gen import build_command_group

registry = build_command_group(spec="openapi.yaml", name="mycli")
# Returns {group: {command: CommandInfo}} — integrate with your existing argparse CLI
```

## Authentication

Auth auto-configures from your spec's `securitySchemes`:

```bash
# Via environment variable
export MYCLI_TOKEN=sk-xxx
mycli users list

# Via flag (overrides env var)
mycli users list --token sk-xxx
```

Supports bearer tokens and API keys. OAuth2 coming in a future release.

## How It Works

1. Reads your OpenAPI spec (YAML or JSON)
2. Resolves all `$ref` references
3. Groups endpoints by tag into command groups
4. Flattens request body schemas into CLI flags (using pydantic-settings)
5. Builds a CLI with manual dispatch for `mycli <group> <command> --flags`

## Status

Early release (v0.0.1). Core features work. [Issues and feedback welcome.](https://github.com/shivaam/openapi-cli-gen/issues)

## License

MIT
