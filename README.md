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
# Recommended: pipx (installs in isolated environment)
pipx install openapi-cli-gen

# Or with uv
uv tool install openapi-cli-gen

# Or in a virtual environment
pip install openapi-cli-gen
```

## Try It Now

Point at any public API — no setup, no files needed:

```bash
# Get a random cat fact
openapi-cli-gen run --spec https://catfact.ninja/docs --base-url https://catfact.ninja Facts get-random

# Browse cat breeds as a table
openapi-cli-gen run --spec https://catfact.ninja/docs --base-url https://catfact.ninja Breeds get --limit 5 --output-format table
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

## Pre-Built CLIs

We publish ready-to-use CLI wrappers for popular APIs, generated with this tool. Install one and start using it instantly:

```bash
# Full-coverage CLI for the OpenAI REST API
pipx install openai-rest-cli
export OPENAI_REST_CLI_TOKEN=sk-...
openai-rest-cli Chat create-completion --model gpt-4o-mini --messages '[{"role":"user","content":"Hi"}]'
```
**[openai-rest-cli](https://github.com/shivaam/openai-rest-cli)** — every OpenAI endpoint (chat, embeddings, images, moderations, files, vector stores, batch) exposed as a typed command. [PyPI](https://pypi.org/project/openai-rest-cli/)

```bash
# Full-coverage CLI for Meilisearch
pipx install meilisearch-rest-cli
meilisearch-rest-cli Health get
```
**[meilisearch-rest-cli](https://github.com/shivaam/meilisearch-rest-cli)** — every Meilisearch REST endpoint, generated from their official OpenAPI spec. [PyPI](https://pypi.org/project/meilisearch-rest-cli/)

More CLIs coming: Qdrant, Typesense, Airflow.

## Tested Against Real APIs

**36/36 regression tests passing across 6 live APIs.** Full CRUD validated — not just reads.

| API | Type | Tests | Notes |
|---|---|---|---|
| **OpenAI** | AI/LLM | 8/8 | Models, Chat Completions, Embeddings, Images (DALL-E), Moderations, Files, Vector Stores |
| **Qdrant** | Vector DB | 14/14 | Collections + Points CRUD, semantic search with real similarity scores |
| **Meilisearch** | Search | 7/7 | Health, version, indexes, documents, tasks, stats |
| **Typesense** | Search | 1/1 | Manually verified, health works live |
| **GitHub** | Public | 6/6 | Meta, licenses, users, rate limit, zen, octocat |
| **Apache Airflow 3.2.0** | Workflow | 26/27 | Full CRUD: create/patch/delete connections, trigger DAG runs |

**Real commands that work today:**

```bash
# OpenAI Chat — one command, real GPT-4o-mini response
openapi-cli-gen run --spec <openai-spec> Chat create-completion \
  --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Hello"}]'

# Qdrant vector search — create collection, insert vectors, semantic search
openapi-cli-gen run --spec <qdrant-spec> --base-url http://localhost:6333 \
  Collections create --collection-name pets --vectors '{"size": 4, "distance": "Cosine"}'

openapi-cli-gen run --spec <qdrant-spec> --base-url http://localhost:6333 \
  Search query-points --collection-name pets --query '[0.1, 0.2, 0.3, 0.4]' --limit 5

# Airflow — trigger a DAG with datetime params
openapi-cli-gen run --spec <airflow-spec> --base-url http://localhost:28080 \
  DagRun trigger-dag-run --dag-id my_dag --logical-date 2026-04-09T12:00:00+00:00

# GitHub — public API, no auth needed
openapi-cli-gen run --spec <github-spec> --base-url https://api.github.com \
  users users/get-by-username --username torvalds
```

See [CHANGELOG.md](CHANGELOG.md) for the full list of bug fixes and improvements.

## Compared to Alternatives

| Feature | openapi-cli-gen | specli | restish | Stainless |
|---|---|---|---|---|
| Nested model flattening | All depths | Scalars only | No | 2 levels |
| Generates distributable code | Yes | No | No | Yes |
| Runtime mode (no codegen) | Yes | Yes | Yes | No |
| Pluggable into existing CLI | Yes | No | No | No |
| Open source | Yes | Yes | Yes | No |

## Status

Early release. Core features work. [Issues and feedback welcome.](https://github.com/shivaam/openapi-cli-gen/issues)

## License

MIT
