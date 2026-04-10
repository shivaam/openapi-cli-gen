# immich-rest-cli

**A full-coverage CLI for the [Immich](https://immich.app) REST API.** Every endpoint in Immich's OpenAPI spec — ~250 subcommands across 35+ groups — exposed as a typed shell command. Generated from [Immich's official OpenAPI spec](https://github.com/immich-app/immich/tree/main/open-api) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

Immich ships an [official CLI](https://github.com/immich-app/CLI) focused on **bulk photo uploading from a directory**. It's the right tool for the classic "initial import from my hard drive" workflow and this CLI is **not trying to replace it**.

This CLI is for everything else the official CLI doesn't cover — scripting against albums, libraries, users, search, tags, memories, sync, admin, workflows, server config, and yes, individual asset uploads too. If you've ever wanted to:

- Write a shell script that creates an album, adds specific assets to it, then shares it with a list of users
- Dump all your library metadata to JSON for an external tool
- Bulk-tag assets from a CSV via a loop
- Automate admin tasks (create users, set quotas, rotate API keys) in Ansible
- Query asset metadata / EXIF from CI pipelines
- Build a digital photo frame script that fetches a rotating "favorites" album
- Sync Immich state into / out of another system

…this gives you the full REST surface as shell commands instead of making you write Python against the OpenAPI client every time.

## Install

```bash
pipx install immich-rest-cli

# Or with uv
uv tool install immich-rest-cli
```

## Setup

Point it at your Immich instance:

```bash
export IMMICH_REST_CLI_BASE_URL=http://your-immich-host:2283/api
```

### Authentication

Immich supports multiple auth modes. This CLI uses **Bearer tokens**:

```bash
export IMMICH_REST_CLI_TOKEN=your-access-token
```

You can get a token two ways:

1. **Log in via this CLI and copy the `accessToken` from the response:**
   ```bash
   immich-rest-cli authentication login --email you@example.com --password ...
   # copy the accessToken from the JSON response
   ```

2. **Create a long-lived API key from the Immich web UI** (Account Settings → API Keys) and use that value.

## Quick Start

All commands below have been verified against a live Immich v2.7 instance.

```bash
# Server health
immich-rest-cli server ping
immich-rest-cli server get-version
immich-rest-cli server get-about-info

# Who am I
immich-rest-cli users get-my

# List albums
immich-rest-cli albums get-all

# Create an album
immich-rest-cli albums create --album-name "Holiday 2025"

# Add assets to an album (--root because the body takes a list of asset IDs)
immich-rest-cli albums add-assets-to-album \
  --id <album-id> \
  --root '{"ids": ["<asset-id-1>", "<asset-id-2>"]}'

# Search
immich-rest-cli search assets --root '{"query": "sunset"}'
immich-rest-cli search smart --root '{"query": "dog on a beach"}'

# Upload a photo (multipart — all metadata flags are required by Immich)
immich-rest-cli assets upload \
  --asset-data ~/Pictures/photo.jpg \
  --device-asset-id "unique-id-1" \
  --device-id "my-script" \
  --file-created-at 2026-04-10T00:00:00.000Z \
  --file-modified-at 2026-04-10T00:00:00.000Z \
  --filename photo.jpg

# Get asset info back
immich-rest-cli assets get-info --id <asset-id>

# List assets by device (useful to find what your own script uploaded)
immich-rest-cli assets get-all-user-by-device-id --device-id my-script

# Admin: list users
immich-rest-cli users-admin search-users-admin
```

## Discover All Commands

```bash
# Top-level command groups (35+)
immich-rest-cli --help

# Commands in a group
immich-rest-cli albums --help

# Flags for a specific command
immich-rest-cli assets upload --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
immich-rest-cli albums get-all --output-format json    # default
immich-rest-cli albums get-all --output-format table   # rich table
immich-rest-cli albums get-all --output-format yaml
immich-rest-cli albums get-all --output-format raw
```

## Command Groups

Full Immich REST surface. A partial list:

| Group | What it covers |
|---|---|
| `authentication` | Login, logout, sign-up, OAuth, session locks, PIN codes |
| `authentication-admin` | Admin-only OAuth unlinking |
| `assets` | Upload, download, delete, search, bulk metadata, edits, stacks |
| `albums` | Full CRUD + add/remove assets + share with users |
| `search` | Metadata search, smart (semantic) search, explore, suggestions |
| `libraries` | External library create/scan/validate |
| `tags` | Tag CRUD + bulk tag/untag assets |
| `memories` | Memory CRUD + asset add/remove |
| `people` | Face recognition, merge, reassign, person CRUD |
| `faces` | Face CRUD + reassignment |
| `partners` | Partner shares |
| `shared-links` | Public share link management |
| `stacks` | Asset stacks (burst photos, raw+jpeg pairs) |
| `timeline` | Time bucket queries for the timeline view |
| `sync` | Bidirectional sync for mobile / desktop clients |
| `trash` | Soft-delete management |
| `notifications` | User + admin notifications |
| `notifications-admin` | Create + test admin notifications |
| `system-config` | Server config — read, update, defaults, storage templates |
| `system-metadata` | Admin onboarding, version check state, reverse geocoding |
| `jobs` / `queues` | Background job management |
| `maintenance-admin` | Maintenance mode, prior install detection |
| `users` / `users-admin` | User CRUD, preferences, profile images, sessions, licenses |
| `database-backups-admin` | List, download, upload, restore backups |
| `api-keys` | User + admin API key management |
| `server` | Version, features, statistics, storage, licensing, theme, APK links |
| `views` | Original-path asset browsing |
| `workflows` | Automation workflows |
| `download` | Archive download for assets |
| `map` | Map markers + reverse geocode |
| `activities` | Comments / likes on shared assets |
| `plugins` | Plugin discovery + triggers |
| `sessions` | User session management |
| `duplicates` | Duplicate detection and resolution |

…and more. Run `immich-rest-cli --help` for the complete list.

## Real Example: Upload an Asset End-to-End

This is the exact flow verified against a live Immich v2.7 instance:

```bash
# Sign up (first user becomes admin)
$ immich-rest-cli authentication sign-up-admin \
    --email admin@example.com \
    --password 'SecurePass123!' \
    --name Admin
{"id": "2a504424-...", "email": "admin@example.com", "isAdmin": true, ...}

# Log in to get a token
$ immich-rest-cli authentication login \
    --email admin@example.com \
    --password 'SecurePass123!'
{"accessToken": "OXiyVeZZ7QO...", "userId": "2a504424-...", ...}

# Export the token
$ export IMMICH_REST_CLI_TOKEN=OXiyVeZZ7QO...

# Upload a photo
$ immich-rest-cli assets upload \
    --asset-data /tmp/photo.jpg \
    --device-asset-id "my-device-001" \
    --device-id "script" \
    --file-created-at 2026-04-10T00:00:00.000Z \
    --file-modified-at 2026-04-10T00:00:00.000Z \
    --filename photo.jpg
{"id": "529cbc25-df58-48e1-9c9c-b8097e7142e9", "status": "created"}

# Read it back
$ immich-rest-cli assets get-info --id 529cbc25-df58-48e1-9c9c-b8097e7142e9
{
  "id": "529cbc25-...",
  "type": "IMAGE",
  "originalFileName": "photo.jpg",
  "fileCreatedAt": "2026-04-10T00:00:00.000Z",
  "exifInfo": {"fileSizeInByte": 7549, "mimeType": "image/jpeg"},
  ...
}
```

## Passing Complex JSON Bodies

Endpoints like `albums add-assets-to-album`, `search assets`, `assets bulk-metadata`, `memories search` take typed request bodies whose schemas are dicts of IDs, filters, or user-defined queries. For these, pass a JSON string to `--root`:

```bash
immich-rest-cli albums add-assets-to-album --id <album-id> --root '{"ids": ["asset-1", "asset-2"]}'

immich-rest-cli search smart --root '{"query": "sunset at the beach", "size": 20}'

immich-rest-cli assets bulk-metadata --root '{"ids": ["asset-1"], "isFavorite": true}'
```

Simple endpoints (like `albums create`, `assets upload`) take typed flags directly.

## How It Works

This package is a thin wrapper:
- Embeds the Immich OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Handles multipart/form-data upload with native httpx multipart support

Since it's spec-driven, new Immich endpoints show up automatically on regeneration — no manual wrapping to fall behind.

## Relationship to the Official Immich CLI

| | Official [@immich/cli](https://github.com/immich-app/CLI) | immich-rest-cli |
|---|---|---|
| Language | TypeScript/Node.js | Python |
| Primary use | Bulk photo import from a folder | Any REST endpoint as a shell command |
| Endpoint coverage | Upload-focused | Every endpoint in the spec (~250) |
| Maintained by | Immich team (official) | Community (unofficial) |

**If you just want to bulk-upload a folder of photos:** use the official CLI. It handles concurrency, deduplication, resume, and is first-party.

**If you want to script against the rest of the API:** use this. They're complementary, not competing.

## Limitations

- **Authenticated session cookies**: use Bearer tokens or long-lived API keys instead. The cookie-based flow (browser sessions) is not wired into the CLI.
- **Server-sent events / streaming endpoints**: not supported. A handful of endpoints stream progress; for those, use the Immich SDK or raw httpx.

## License

MIT. Not affiliated with Immich — this is an unofficial community CLI built on top of their public OpenAPI spec.
