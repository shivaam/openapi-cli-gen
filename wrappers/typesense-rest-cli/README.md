# typesense-rest-cli

**A full-coverage CLI for the [Typesense](https://typesense.org) search engine REST API.** Every endpoint in Typesense's OpenAPI spec, exposed as a typed command. Generated from [Typesense's official OpenAPI spec](https://github.com/typesense/typesense-api-spec) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

Typesense has client libraries for most popular languages, but no REST CLI. For shell scripts, CI automation, index bootstrapping, and ad-hoc admin tasks, most people hand-roll `curl` with their API key in a header and hope they spelled the JSON right.

This CLI gives you the entire Typesense REST surface as typed shell commands — collections, documents, searches, aliases, keys, stopwords, analytics, conversations — no SDK, no boilerplate. When Typesense adds endpoints, a regeneration picks them up.

## Install

```bash
pipx install typesense-rest-cli

# Or with uv
uv tool install typesense-rest-cli
```

## Setup

Point it at your Typesense instance (default is `http://localhost:8108`):

```bash
export TYPESENSE_REST_CLI_BASE_URL=http://localhost:8108
```

### Authentication — important

Typesense uses an API key header (`X-TYPESENSE-API-KEY`), which this CLI maps to:

```bash
export TYPESENSE_REST_CLI_API_KEY=your-api-key
```

**Note the env var name — it's `_API_KEY`, not `_TOKEN`.** Typesense's spec uses an `apiKey` security scheme (not bearer), so the convention matches.

## Quick Start

```bash
# Server health
typesense-rest-cli health health

# Create a collection (schema-driven)
typesense-rest-cli collections create \
  --name books \
  --fields '[
    {"name": "title",  "type": "string"},
    {"name": "author", "type": "string", "facet": true},
    {"name": "year",   "type": "int32"}
  ]' \
  --default-sorting-field year

# List all collections
typesense-rest-cli collections get-collections

# Get a specific collection's schema + doc count
typesense-rest-cli collections get-collection --collection-name books

# Upsert a document
typesense-rest-cli documents index --collection-name books --root '{
  "id": "1",
  "title": "The Pragmatic Programmer",
  "author": "Hunt & Thomas",
  "year": 1999
}'

# Search the collection
typesense-rest-cli documents search-collection \
  --collection-name books \
  --q programmer \
  --query-by title,author

# Delete a collection
typesense-rest-cli collections delete --collection-name books
```

## Discover All Commands

```bash
# Top-level groups
typesense-rest-cli --help

# Commands in a group
typesense-rest-cli collections --help

# Flags for a specific command
typesense-rest-cli documents search-collection --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
typesense-rest-cli collections get-collections --output-format table
typesense-rest-cli collections get-collections --output-format yaml
typesense-rest-cli collections get-collections --output-format raw
```

## Command Groups

| Group | What it covers |
|---|---|
| `health` | Liveness probe |
| `collections` | Full CRUD for collections + schema |
| `documents` | Index, upsert, get, delete, search, import |
| `curation` | Override search results |
| `aliases` | Collection aliases (blue/green indexing) |
| `synonyms` | Per-collection synonym sets |
| `stopwords` | Stopword management |
| `keys` | API key creation + scoping |
| `multi-search` | Federated search across collections |
| `analytics` | Analytics rules (click / search events) |
| `presets` | Reusable search parameter presets |
| `conversations` | Conversational search models |
| `debug` | Debug, metrics, stats |
| `operations` | Snapshot, vote, re-elect leader |
| `cluster` | Cluster-wide health + vote |

## Passing Complex JSON Bodies

Document imports and search parameter objects with nested schemas accept a JSON string via `--root`:

```bash
typesense-rest-cli documents index --collection-name books --root '{"id": "1", ...}'
```

Flat endpoints (like `collections create`) take typed flags directly.

## How It Works

This package is a thin wrapper:
- Embeds the Typesense OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Default base URL: `http://localhost:8108`

Since it's spec-driven, new Typesense endpoints show up automatically on regeneration.

## License

MIT. Not affiliated with Typesense — this is an unofficial community CLI built on top of their public OpenAPI spec.
