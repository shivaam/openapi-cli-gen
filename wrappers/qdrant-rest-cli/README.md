# qdrant-rest-cli

**A full-coverage CLI for the [Qdrant](https://qdrant.tech) vector database REST API.** Every endpoint in Qdrant's OpenAPI spec, exposed as a typed command. Generated from [Qdrant's official OpenAPI spec](https://github.com/qdrant/qdrant/tree/master/docs/redoc) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

Qdrant ships excellent client SDKs (Python, Rust, Go, JS), but no REST CLI. For shell scripting, Makefile targets, CI pipelines, and interactive ad-hoc queries, most people drop to raw `curl` and hand-build JSON payloads.

This CLI gives you the entire Qdrant REST API as flat shell commands with typed flags — collections, points, search, snapshots, distributed cluster ops — without writing any Python or curl boilerplate. When Qdrant adds endpoints, a regeneration picks them up.

## Install

```bash
pipx install qdrant-rest-cli

# Or with uv
uv tool install qdrant-rest-cli
```

## Setup

Point it at your Qdrant instance (default is `http://localhost:6333`):

```bash
export QDRANT_REST_CLI_BASE_URL=http://localhost:6333
```

If your instance uses an API key:

```bash
export QDRANT_REST_CLI_API_KEY=your-api-key
```

The CLI sends it as the `api-key` header automatically, matching Qdrant's security scheme.

## Quick Start

All commands below have been verified against a live Qdrant instance.

```bash
# Server health
qdrant-rest-cli service root
qdrant-rest-cli service healthz

# List collections
qdrant-rest-cli collections get-collections

# Create a collection (4-dim vectors, cosine distance)
qdrant-rest-cli collections create \
  --collection-name pets \
  --vectors '{"size": 4, "distance": "Cosine"}'

# Upsert points with payloads (use --root for the full JSON request body)
qdrant-rest-cli points upsert --collection-name pets --root '{
  "points": [
    {"id": 1, "vector": [0.9, 0.1, 0.1, 0.1], "payload": {"name": "cat",  "species": "mammal"}},
    {"id": 2, "vector": [0.1, 0.9, 0.1, 0.1], "payload": {"name": "dog",  "species": "mammal"}},
    {"id": 3, "vector": [0.1, 0.1, 0.9, 0.1], "payload": {"name": "bird", "species": "avian"}}
  ]
}'

# Count points
qdrant-rest-cli points count --collection-name pets

# Semantic search — return results WITH their payloads
qdrant-rest-cli search points \
  --collection-name pets \
  --vector '[0.85, 0.15, 0.1, 0.1]' \
  --limit 2 \
  --with-payload true

# Scroll through all points
qdrant-rest-cli points scroll --collection-name pets --limit 10

# Get a collection's info
qdrant-rest-cli collections get-collection --collection-name pets

# Delete the collection
qdrant-rest-cli collections delete --collection-name pets
```

## Discover All Commands

```bash
# Top-level groups
qdrant-rest-cli --help

# Commands in a group
qdrant-rest-cli collections --help

# Flags for a specific command
qdrant-rest-cli search points --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
qdrant-rest-cli collections get-collections --output-format table
qdrant-rest-cli collections get-collections --output-format yaml
qdrant-rest-cli collections get-collections --output-format raw
```

## Command Groups

| Group | What it covers |
|---|---|
| `service` | Server root, health (`healthz`, `livez`, `readyz`), telemetry, metrics |
| `collections` | Full CRUD for collections + optimizations |
| `aliases` | Collection aliases |
| `points` | Upsert, get, delete, scroll, count, batch operations, payload/vector updates, facets |
| `search` | Query points, batch search, recommend, discover, point groups, matrices |
| `snapshots` | Create / list / delete / restore snapshots (collection + shard level) |
| `distributed` | Cluster status, peer management, shard keys |
| `indexes` | Payload index create/delete |
| `beta` | Issue tracking for the running instance |

## Passing Complex JSON Bodies

Most Qdrant write endpoints take deeply nested request bodies (lists of points, complex filters, hybrid queries). For these, pass the entire body as a JSON string via `--root`:

```bash
qdrant-rest-cli points upsert --collection-name pets --root '{"points":[...]}'

qdrant-rest-cli search points --collection-name pets --root '{
  "vector": [0.85, 0.15, 0.1, 0.1],
  "limit": 5,
  "with_payload": true,
  "filter": {"must": [{"key": "species", "match": {"value": "mammal"}}]}
}'
```

Flat endpoints (like `collections create`) accept typed flags directly — use whichever is clearer for a given call.

## Real Example: End-to-End Vector Search

```bash
$ qdrant-rest-cli collections create \
    --collection-name movies \
    --vectors '{"size": 4, "distance": "Cosine"}'
{"result": true, "status": "ok", "time": 0.012}

$ qdrant-rest-cli points upsert --collection-name movies --root '{
    "points": [
      {"id": 1, "vector": [0.9, 0.1, 0.1, 0.1], "payload": {"title": "The Matrix"}},
      {"id": 2, "vector": [0.1, 0.9, 0.1, 0.1], "payload": {"title": "Titanic"}}
    ]
  }'
{"result": {"operation_id": 0, "status": "completed"}, "status": "ok"}

$ qdrant-rest-cli search points --collection-name movies \
    --vector '[0.85, 0.15, 0.1, 0.1]' \
    --limit 2 \
    --with-payload true
{
  "result": [
    {"id": 1, "score": 0.998, "payload": {"title": "The Matrix"}},
    {"id": 2, "score": 0.299, "payload": {"title": "Titanic"}}
  ],
  "status": "ok"
}
```

## How It Works

This package is a thin wrapper:
- Embeds the Qdrant OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Default base URL: `http://localhost:6333`

Since it's spec-driven, new Qdrant endpoints show up automatically on regeneration — no manual wrapping to fall behind.

## License

MIT. Not affiliated with Qdrant — this is an unofficial community CLI built on top of their public OpenAPI spec.
