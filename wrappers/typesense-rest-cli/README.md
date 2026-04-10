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

All commands below have been verified against a live Typesense instance.

```bash
# Server health
typesense-rest-cli health health

# Create a collection with a typed schema
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

# Index a document (use --root for the JSON body)
typesense-rest-cli documents index --collection-name books --root '{
  "id": "1",
  "title": "The Pragmatic Programmer",
  "author": "Hunt and Thomas",
  "year": 1999
}'

# Index another
typesense-rest-cli documents index --collection-name books --root '{
  "id": "2",
  "title": "Clean Code",
  "author": "Robert Martin",
  "year": 2008
}'

# Search — note that `q` is a single-char flag, so use -q (short form)
typesense-rest-cli documents search-collection \
  --collection-name books \
  -q code \
  --query-by title,author

# Delete the collection
typesense-rest-cli collections delete --collection-name books
```

### The `-q` vs `--q` gotcha

Typesense's search endpoint uses a single-character query parameter `q`. Python's argparse treats single-character flags as short-form options, so you invoke it as `-q code` (one dash), not `--q code`. The `--help` output shows `[-q str]` — follow that.

## Discover All Commands

```bash
# Top-level groups
typesense-rest-cli --help

# Commands in a group
typesense-rest-cli collections --help

# Flags for a specific command
typesense-rest-cli documents search-collection --help
```

`documents search-collection` exposes all ~70 search parameters as individual flags (`--query-by`, `--filter-by`, `--sort-by`, `--facet-by`, `--include-fields`, etc.).

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
| `collections` | Full CRUD for collections + aliases (blue/green indexing) |
| `documents` | Index, upsert, get, delete, search, import, multi-search |
| `analytics` | Analytics rules + events (click / search tracking) |
| `keys` | API key creation + scoping |
| `curation-sets` | Override / promote search results |
| `synonyms` | Per-collection synonym sets |
| `stopwords` | Stopword management |
| `presets` | Reusable search parameter presets |
| `conversations` | Conversational search models |
| `nl-search-models` | Natural-language search models |
| `stemming` | Stemming dictionaries |
| `operations` | Snapshot, vote, re-elect leader, cache, slow-request log |
| `debug` | Debug info |

## Passing Complex JSON Bodies

Most `documents` write endpoints take raw documents whose schema is user-defined — the generator can't produce typed flags for them. Use `--root` with a JSON string:

```bash
typesense-rest-cli documents index --collection-name books --root '{"id":"1", ...}'
typesense-rest-cli documents update-document --collection-name books --document-id 1 --root '{"year":2024}'
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
