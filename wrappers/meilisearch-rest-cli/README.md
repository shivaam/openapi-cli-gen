# meilisearch-rest-cli

**A full-coverage CLI for the [Meilisearch](https://www.meilisearch.com) REST API.** Every endpoint in the official OpenAPI spec, exposed as a flat command with typed flags.

Generated from [Meilisearch's official OpenAPI spec](https://github.com/meilisearch/open-api) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

Meilisearch has been asked for a CLI for years ([roadmap request](https://roadmap.meilisearch.com/c/136-meilisearch-command-line-interface-cli)). Meanwhile, users drop to `curl` for admin operations like managing indexes, API keys, tasks, and settings.

This CLI covers every endpoint in the REST API automatically — nothing to maintain, no features skipped. When Meilisearch updates their spec, a regeneration gets you the new commands.

## Install

```bash
pipx install meilisearch-rest-cli

# Or with uv
uv tool install meilisearch-rest-cli
```

## Setup

Point it at your Meilisearch instance (default is `http://localhost:7700`):

```bash
export MEILISEARCH_REST_CLI_BASE_URL=http://localhost:7700
```

### Authentication

If your Meilisearch instance uses an API key, set it via environment variable:

```bash
export MEILISEARCH_REST_CLI_TOKEN=your-master-key
```

The CLI will automatically send it as a Bearer token on every request.

## Quick Start

All commands below have been verified against a live Meilisearch 1.41 instance.

```bash
# Server health + version
meilisearch-rest-cli health get
meilisearch-rest-cli version get

# List all indexes
meilisearch-rest-cli indexes list

# Create an index
meilisearch-rest-cli indexes create-index --uid movies --primary-key id

# Add documents (use --root — document bodies are user-defined, no typed flags)
meilisearch-rest-cli documents replace --index-uid movies --root '[
  {"id": 1, "title": "The Matrix",  "year": 1999},
  {"id": 2, "title": "Inception",   "year": 2010},
  {"id": 3, "title": "Titanic",     "year": 1997}
]'

# Check task status (writes are async; watch for `succeeded` and indexedDocuments)
meilisearch-rest-cli tasks get-tasks --limit 3

# Search — use --root to pass a raw SearchQuery JSON, which dodges the upstream
# snake_case/camelCase field-name mismatch in Meilisearch's own OpenAPI spec
meilisearch-rest-cli indexes search-with-post --index-uid movies --root '{
  "q": "matrix",
  "limit": 5
}'

# Stats
meilisearch-rest-cli stats get
meilisearch-rest-cli stats get-index --index-uid movies

# Delete the index
meilisearch-rest-cli indexes delete-index --index-uid movies
```

## A note on `--root` for searches

Meilisearch's official OpenAPI spec declares `SearchQuery` field names in `snake_case` (`retrieve_vectors`, `hits_per_page`, `attributes_to_retrieve`...) but the Meilisearch server actually expects `camelCase` on the wire (`retrieveVectors`, `hitsPerPage`, `attributesToRetrieve`). This is an upstream spec bug — not specific to this CLI.

The `--root` flag lets you bypass that mismatch entirely: pass a camelCase JSON payload that matches the actual server API, and the CLI sends it verbatim:

```bash
meilisearch-rest-cli indexes search-with-post --index-uid movies --root '{
  "q": "matrix",
  "limit": 10,
  "offset": 0,
  "attributesToRetrieve": ["title", "year"],
  "showRankingScore": true
}'
```

Once Meilisearch fixes their spec, the typed flags will work too. Until then, use `--root` for searches.

## Discover All Commands

```bash
# Top-level groups
meilisearch-rest-cli --help

# Commands in a group
meilisearch-rest-cli indexes --help

# Flags for a specific command
meilisearch-rest-cli indexes create-index --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
meilisearch-rest-cli indexes list --output-format table
meilisearch-rest-cli indexes list --output-format yaml
meilisearch-rest-cli indexes list --output-format raw
```

## Command Groups

| Group | What it covers |
|---|---|
| `health` | Server health check |
| `version` | Server version info |
| `stats` | Database + per-index stats + metrics |
| `indexes` | CRUD for indexes + `search-with-post` / `search-with-url-query` / `swap` |
| `documents` | Add / update / replace / delete / query / get documents |
| `settings` | All index settings (70+ commands: facet-search, embedders, synonyms, stop-words, ranking-rules, proximity-precision, prefix-search, filterable/sortable/searchable attributes, etc.) |
| `tasks` | List, query, cancel, delete tasks |
| `batches` | Batch info |
| `keys` | API key management |
| `snapshots` | Create snapshots |
| `dumps` | Create dumps |
| `experimental-features` | Enable / disable experimental features |
| `multi-search` | Search multiple indexes in one request |
| `facet-search` | Faceted search |
| `similar-documents` | Find similar documents (semantic) |
| `logs` | Configure and stream logs |
| `network` | Remote instance network config |

## How It Works

This package is a thin wrapper:
- Embeds the Meilisearch OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Pre-configures the base URL for local Meilisearch

If you want to generate a CLI for any other OpenAPI spec, check out [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## License

MIT. Not affiliated with Meilisearch — this is an unofficial community CLI built on top of their public OpenAPI spec.
