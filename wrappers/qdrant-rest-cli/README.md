# qdrant-rest-cli

**A full-coverage CLI for the [Qdrant](https://qdrant.tech) vector database REST API.** Every endpoint in Qdrant's OpenAPI spec, exposed as a typed command. Generated from [Qdrant's official OpenAPI spec](https://github.com/qdrant/qdrant/tree/master/docs/redoc) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

Qdrant ships excellent client SDKs (Python, Rust, Go, JS), but no REST CLI. For shell scripting, Makefile targets, CI pipelines, and interactive ad-hoc queries, most people drop to raw `curl` and hand-build JSON payloads.

This CLI gives you the entire Qdrant REST API as flat shell commands with typed flags — collections, points, snapshots, cluster, shards — without writing any Python or curl boilerplate. When Qdrant adds endpoints, a regeneration picks them up.

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

# Upsert points with payloads
qdrant-rest-cli points upsert --collection-name pets --root '{
  "points": [
    {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"name": "Rex",   "species": "dog"}},
    {"id": 2, "vector": [0.2, 0.1, 0.4, 0.3], "payload": {"name": "Whiskers", "species": "cat"}}
  ]
}'

# Count points
qdrant-rest-cli points count --collection-name pets

# Semantic search
qdrant-rest-cli points search --collection-name pets \
  --vector '[0.15, 0.15, 0.35, 0.35]' \
  --limit 5

# Scroll through all points
qdrant-rest-cli points scroll --collection-name pets --limit 10

# Get a collection's info
qdrant-rest-cli collections get --collection-name pets

# Delete a collection
qdrant-rest-cli collections delete --collection-name pets
```

## Discover All Commands

```bash
# Top-level groups
qdrant-rest-cli --help

# Commands in a group
qdrant-rest-cli collections --help

# Flags for a specific command
qdrant-rest-cli points search --help
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
| `service` | Server root, health, telemetry, metrics, readiness |
| `collections` | Full CRUD for collections + aliases + info |
| `points` | Upsert, get, delete, scroll, count, batch operations |
| `search` | Vector search, recommend, discover, query |
| `snapshots` | Create / list / delete / download snapshots |
| `cluster` | Cluster status, peer management |
| `shards` | Shard key operations |
| `indexes` | Payload index management |

## Passing Complex JSON Bodies

Qdrant endpoints with deeply nested unions (like `points upsert`, batch operations) accept a JSON string via `--root`:

```bash
qdrant-rest-cli points upsert --collection-name pets --root '{
  "points": [...]
}'
```

Flat endpoints (like `collections create`) accept typed flags directly:

```bash
qdrant-rest-cli collections create --collection-name pets --vectors '{"size": 4, "distance": "Cosine"}'
```

Both styles work; use whichever is clearer for a given call.

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

$ qdrant-rest-cli points search --collection-name movies \
    --vector '[0.85, 0.15, 0.1, 0.1]' \
    --limit 2
{
  "result": [
    {"id": 1, "score": 0.998, "payload": {"title": "The Matrix"}},
    {"id": 2, "score": 0.204, "payload": {"title": "Titanic"}}
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
