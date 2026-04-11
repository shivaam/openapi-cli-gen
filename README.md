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
openapi-cli-gen run --spec https://catfact.ninja/docs --base-url https://catfact.ninja \
  facts get-random

# Browse cat breeds as a table
openapi-cli-gen run --spec https://catfact.ninja/docs --base-url https://catfact.ninja \
  breeds get --limit 5 --output-format table
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

Six ready-to-use CLI wrappers, each generated from its API's official OpenAPI spec. Install one and start using it instantly:

```bash
# OpenAI — every endpoint (chat, embeddings, images, audio, files,
# vector stores, batch, fine-tuning, ...) as a typed subcommand
pipx install openai-rest-cli
export OPENAI_REST_CLI_TOKEN=sk-...
openai-rest-cli chat create-completion --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Hi"}]'
```

```bash
# Qdrant — collections, points, search, snapshots, distributed
pipx install qdrant-rest-cli
qdrant-rest-cli collections get-collections
qdrant-rest-cli search points --collection-name pets \
  --vector '[0.1,0.2,0.3,0.4]' --limit 5 --with-payload true
```

```bash
# Meilisearch — indexes, documents, search, settings, tasks
pipx install meilisearch-rest-cli
meilisearch-rest-cli indexes list
meilisearch-rest-cli documents replace --index-uid movies \
  --root '[{"id":1,"title":"The Matrix"}]'
```

```bash
# Typesense — collections, documents, search (72 search flags typed)
pipx install typesense-rest-cli
export TYPESENSE_REST_CLI_API_KEY=xyz
typesense-rest-cli documents search-collection --collection-name books \
  -q programmer --query-by title,author
```

```bash
# AdGuard Home — filtering, clients, DHCP, rewrite, TLS, stats
pipx install adguard-home-cli
export ADGUARD_HOME_CLI_USERNAME=admin
export ADGUARD_HOME_CLI_PASSWORD=xxx
adguard-home-cli filtering add-url --name "OISD" --url "https://big.oisd.nl/" --no-whitelist
```

```bash
# Immich — ~250 subcommands across 36 groups including multipart upload
pipx install immich-rest-cli
export IMMICH_REST_CLI_TOKEN=your-key
immich-rest-cli assets upload --asset-data photo.jpg \
  --device-asset-id "id-1" --device-id "script" \
  --file-created-at 2026-04-10T00:00:00.000Z \
  --file-modified-at 2026-04-10T00:00:00.000Z --filename photo.jpg
```

Each wrapper's source README (install, auth, real verified commands) lives under [wrappers/](wrappers/) in this monorepo.

| Wrapper | PyPI | Source |
|---|---|---|
| openai-rest-cli | [pypi](https://pypi.org/project/openai-rest-cli/) | [wrappers/openai-rest-cli/](wrappers/openai-rest-cli/) |
| qdrant-rest-cli | [pypi](https://pypi.org/project/qdrant-rest-cli/) | [wrappers/qdrant-rest-cli/](wrappers/qdrant-rest-cli/) |
| meilisearch-rest-cli | [pypi](https://pypi.org/project/meilisearch-rest-cli/) | [wrappers/meilisearch-rest-cli/](wrappers/meilisearch-rest-cli/) |
| typesense-rest-cli | [pypi](https://pypi.org/project/typesense-rest-cli/) | [wrappers/typesense-rest-cli/](wrappers/typesense-rest-cli/) |
| adguard-home-cli | [pypi](https://pypi.org/project/adguard-home-cli/) | [wrappers/adguard-home-cli/](wrappers/adguard-home-cli/) |
| immich-rest-cli | [pypi](https://pypi.org/project/immich-rest-cli/) | [wrappers/immich-rest-cli/](wrappers/immich-rest-cli/) |

## Tested Against Real APIs

**36/36 regression tests passing across 6 live APIs.** Full CRUD validated — not just reads.

| API | Type | Tests | Notes |
|---|---|---|---|
| **OpenAI** | AI/LLM | 8/8 | Models, Chat Completions, Embeddings, Images (DALL-E), Moderations, Files, Vector Stores |
| **Qdrant** (collections) | Vector DB | 7/7 | Service root, healthz, collections CRUD, exists |
| **Qdrant Points** | Vector DB | 7/7 | Upsert, get, scroll, count, query-points, cleanup — vector search with real similarity scores |
| **Meilisearch** | Search | 7/7 | Health, version, indexes, stats, tasks |
| **Typesense** | Search | 1/1 | Health verified live; `documents index --root` + `search-collection -q ...` verified via wrapper |
| **GitHub** | Public | 6/6 | Meta, licenses, users, rate limit, zen, octocat |

**Real commands that work today:**

```bash
# OpenAI Chat — one command, real GPT-4o-mini response
openapi-cli-gen run --spec <openai-spec> chat create-completion \
  --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Hello"}]'

# Qdrant vector search — create collection, insert vectors, semantic search
openapi-cli-gen run --spec <qdrant-spec> --base-url http://localhost:6333 \
  collections create --collection-name pets \
  --vectors '{"size": 4, "distance": "Cosine"}'

openapi-cli-gen run --spec <qdrant-spec> --base-url http://localhost:6333 \
  search query-points --collection-name pets \
  --query '[0.1, 0.2, 0.3, 0.4]' --limit 5

# Meilisearch — add documents and search, verified against live 1.41
openapi-cli-gen run --spec <meili-spec> --base-url http://localhost:7700 \
  documents replace --index-uid movies \
  --root '[{"id":1,"title":"The Matrix"}]'

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
