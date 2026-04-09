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

## Install

```bash
pip install openapi-cli-gen
```

## Try It Now

Point at any public API — no setup, no files needed:

```bash
# Get a random cat fact
openapi-cli-gen run --spec https://catfact.ninja/docs Facts get-random --base-url https://catfact.ninja

# Browse cat breeds as a table
openapi-cli-gen run --spec https://catfact.ninja/docs Breeds get --limit 5 --output-format table --base-url https://catfact.ninja
```
```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ breed          ┃ country       ┃ origin         ┃ coat       ┃ pattern       ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Abyssinian     │ Ethiopia      │ Natural/Stand… │ Short      │ Ticked        │
│ Aegean         │ Greece        │ Natural/Stand… │ Semi-long  │ Bi- or tri-…  │
│ American Curl  │ United States │ Mutation       │ Short/Long │ All           │
└────────────────┴───────────────┴────────────────┴────────────┴───────────────┘
```

```bash
# Inspect any spec to see what commands you'd get
openapi-cli-gen inspect --spec https://petstore3.swagger.io/api/v3/openapi.json
```

## Generate Your Own CLI

```bash
openapi-cli-gen generate --spec https://api.example.com/openapi.json --name mycli
cd mycli && pip install -e .
mycli users list
mycli users create --name John --email john@example.com --address.city NYC
```

Ship it to your users: `pip install mycli`.

## Nested Model Flattening

The core feature. Works at any depth:

```bash
--address.city NYC                                  # depth 1
--ceo.name Bob --ceo.email bob@acme.com             # depth 2
--retry.backoff.strategy exponential                 # depth 3
--tags admin --tags reviewer                         # arrays
--environment JAVA_HOME=/usr/lib/jvm                 # dicts
--role admin                                         # enums (validated)
--address '{"street": "123 Main", "city": "NYC"}'   # JSON fallback
```

## As a Library

```python
from openapi_cli_gen import build_cli

app = build_cli(spec="openapi.yaml", name="mycli")
app()
```

Or plug API commands into your existing CLI:

```python
from openapi_cli_gen import build_command_group

registry = build_command_group(spec="openapi.yaml", name="mycli")
```

## Auth

Auto-configures from your spec's `securitySchemes`:

```bash
export MYCLI_TOKEN=sk-xxx    # env var
mycli users list --token sk-xxx  # or flag (overrides env)
```

## Tested Against Real APIs

Live CRUD validated against **Apache Airflow 3.2.0** (111 endpoints) — create, update, delete connections, trigger DAG runs, manage pools and variables. All pass.

Also parsed: Petstore (19 endpoints), ReqRes (40), Redocly Museum (8), Open-Meteo (1). **182 endpoints across 6 APIs, all specs parse successfully.**

## Compared to Alternatives

| Feature | openapi-cli-gen | specli | restish | Stainless |
|---|---|---|---|---|
| Nested model flattening | All depths | Scalars only | No | 2 levels |
| Generates distributable code | Yes | No | No | Yes |
| Runtime mode (no codegen) | Yes | Yes | Yes | No |
| Pluggable into existing CLI | Yes | No | No | No |
| Open source | Yes | Yes | Yes | No |

## Status

Early release (v0.0.1). Core features work. [Issues and feedback welcome.](https://github.com/shivaam/openapi-cli-gen/issues)

## License

MIT
