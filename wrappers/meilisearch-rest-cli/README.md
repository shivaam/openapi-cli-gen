# meilisearch-rest-cli

**A full-coverage CLI for the Meilisearch REST API.** Every endpoint in the official OpenAPI spec, exposed as a flat command with typed flags.

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

## Quick Start

Point it at your Meilisearch instance:

```bash
export MEILISEARCH_REST_CLI_BASE_URL=http://localhost:7700

# Or use the flag on every call (default is http://localhost:7700)
meilisearch-rest-cli Health get
```

### Common operations

```bash
# Server health + version
meilisearch-rest-cli Health get
meilisearch-rest-cli Version get

# List indexes
meilisearch-rest-cli Indexes list

# Create an index
meilisearch-rest-cli Indexes create-index --uid movies --primary-key id

# Stats (all indexes or per-index)
meilisearch-rest-cli Stats get
meilisearch-rest-cli Stats get-index --index-uid movies

# Tasks
meilisearch-rest-cli Tasks get-tasks --limit 10
meilisearch-rest-cli Tasks get-task --task-uid 42

# Delete an index
meilisearch-rest-cli Indexes delete-index --index-uid movies
```

### Authentication

If your Meilisearch instance uses an API key, set it via environment variable:

```bash
export MEILISEARCH_REST_CLI_TOKEN=your-master-key
```

The CLI will automatically send it as a Bearer token on every request.

### Discover all commands

```bash
# Top-level command groups
meilisearch-rest-cli --help

# Commands in a group
meilisearch-rest-cli Indexes --help

# Flags for a specific command
meilisearch-rest-cli Indexes create-index --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
meilisearch-rest-cli Indexes list --output-format json    # default
meilisearch-rest-cli Indexes list --output-format table   # rich table
meilisearch-rest-cli Indexes list --output-format yaml
meilisearch-rest-cli Indexes list --output-format raw
```

## Command Groups

| Group | Commands |
|---|---|
| Health | Server health check |
| Version | Server version info |
| Stats | Database + per-index stats |
| Indexes | CRUD for indexes |
| Documents | Add/update/delete documents, search |
| Settings | All index settings (filterable attrs, sortable attrs, etc.) |
| Tasks | List, query, cancel tasks |
| Keys | API key management |
| Batches | Batch operations |
| Snapshots | Create snapshots |
| Dumps | Create dumps |
| Experimental features | Enable/disable experimental features |
| Multi-search | Search multiple indexes in one request |
| Facet Search | Faceted search |
| Similar documents | Find similar documents |
| Logs | Configure and stream logs |
| Network | Remote instance config |

## Limitations

- **Complex request bodies**: Some endpoints with deeply nested `oneOf` / `anyOf` schemas accept a JSON string via the `--root` flag instead of individual fields. This is a current limitation of the underlying tool; most common operations use flat flags.
- **Document operations**: Uploading documents uses `--root` with a JSON array.

## How It Works

This package is a thin wrapper:
- Embeds the Meilisearch OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Pre-configures the base URL for local Meilisearch

If you want to generate a CLI for any other OpenAPI spec, check out [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## License

MIT. Not affiliated with Meilisearch — this is an unofficial community CLI built on top of their public OpenAPI spec.

