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
   immich-rest-cli Authentication login --email you@example.com --password ...
   # copy the accessToken from the JSON response
   ```

2. **Create a long-lived API key from the Immich web UI** (Account Settings → API Keys) and use that value.

## Quick Start

```bash
# Server health
immich-rest-cli Server ping
immich-rest-cli Server get-version
immich-rest-cli Server get-about-info

# Who am I
immich-rest-cli Users get-my

# List albums
immich-rest-cli Albums get-all

# Create an album
immich-rest-cli Albums create --album-name "Holiday 2025"

# Add assets to an album
immich-rest-cli Albums add-assets-to-album \
  --id <album-id> \
  --ids '["<asset-id-1>", "<asset-id-2>"]'

# Search
immich-rest-cli Search assets --query "sunset"
immich-rest-cli Search smart --query "dog on a beach"

# Upload a photo (multipart — every field from the spec)
immich-rest-cli Assets upload \
  --asset-data ~/Pictures/photo.jpg \
  --device-asset-id "unique-id-1" \
  --device-id "my-script" \
  --file-created-at 2026-04-10T00:00:00.000Z \
  --file-modified-at 2026-04-10T00:00:00.000Z \
  --filename photo.jpg

# Get asset info back
immich-rest-cli Assets get-info --id <asset-id>

# List assets by device
immich-rest-cli Assets get-all-user-by-device-id --device-id my-script

# Admin: list users
immich-rest-cli "Users (admin)" search-users-admin
```

## Discover All Commands

```bash
# Top-level command groups (35+)
immich-rest-cli --help

# Commands in a group
immich-rest-cli Albums --help

# Flags for a specific command
immich-rest-cli Assets upload --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
immich-rest-cli Albums get-all --output-format json    # default
immich-rest-cli Albums get-all --output-format table   # rich table
immich-rest-cli Albums get-all --output-format yaml
immich-rest-cli Albums get-all --output-format raw
```

## Command Groups

Full Immich REST surface. A partial list:

| Group | What it covers |
|---|---|
| `Authentication` | Login, logout, sign-up, OAuth, session locks, PIN codes |
| `Assets` | Upload, download, delete, search, bulk metadata, edits, stacks |
| `Albums` | Full CRUD + add/remove assets + share with users |
| `Search` | Metadata search, smart (semantic) search, explore, suggestions |
| `Libraries` | External library create/scan/validate |
| `Tags` | Tag CRUD + bulk tag/untag assets |
| `Memories` | Memory CRUD + asset add/remove |
| `People` | Face recognition, merge, reassign, person CRUD |
| `Faces` | Face CRUD + reassignment |
| `Partners` | Partner shares |
| `Shared links` | Public share link management |
| `Stacks` | Asset stacks (burst photos, raw+jpeg pairs) |
| `Timeline` | Time bucket queries for the timeline view |
| `Sync` | Bidirectional sync for mobile / desktop clients |
| `Trash` | Soft-delete management |
| `Notifications` | User + admin notifications |
| `System config` | Server config — read, update, defaults, storage templates |
| `System metadata` | Admin onboarding, version check state, reverse geocoding |
| `Jobs` / `Queues` | Background job management |
| `Maintenance (admin)` | Maintenance mode, prior install detection |
| `Users` / `Users (admin)` | User CRUD, preferences, profile images, sessions, licenses |
| `Database Backups (admin)` | List, download, upload, restore backups |
| `API keys` | User + admin API key management |
| `Server` | Version, features, statistics, storage, licensing, theme, APK links |
| `Views` | Original-path asset browsing |
| `Workflows` | Automation workflows |
| `Download` | Archive download for assets |
| `Map` | Map markers + reverse geocode |
| `Activities` | Comments / likes on shared assets |
| `Plugins` | Plugin discovery + triggers |
| `Sessions` | User session management |
| `Duplicates` | Duplicate detection and resolution |

…and more. Run `immich-rest-cli --help` for the complete list.

## Real Example: Upload an Asset End-to-End

This is the exact flow verified against a live Immich v2 instance:

```bash
# Sign up (first user becomes admin)
$ immich-rest-cli Authentication sign-up-admin \
    --email admin@example.com \
    --password 'SecurePass123!' \
    --name Admin
{"id": "2a504424-...", "email": "admin@example.com", "isAdmin": true, ...}

# Log in to get a token
$ immich-rest-cli Authentication login \
    --email admin@example.com \
    --password 'SecurePass123!'
{"accessToken": "OXiyVeZZ7QO...", "userId": "2a504424-...", ...}

# Export the token
$ export IMMICH_REST_CLI_TOKEN=OXiyVeZZ7QO...

# Upload a photo
$ immich-rest-cli Assets upload \
    --asset-data /tmp/photo.jpg \
    --device-asset-id "my-device-001" \
    --device-id "script" \
    --file-created-at 2026-04-10T00:00:00.000Z \
    --file-modified-at 2026-04-10T00:00:00.000Z \
    --filename photo.jpg
{"id": "1447e90c-65bc-4574-8be5-cd6bb94afcaf", "status": "created"}

# Read it back
$ immich-rest-cli Assets get-info --id 1447e90c-65bc-4574-8be5-cd6bb94afcaf
{
  "id": "1447e90c-...",
  "type": "IMAGE",
  "originalFileName": "photo.jpg",
  "fileCreatedAt": "2026-04-10T00:00:00.000Z",
  "exifInfo": {
    "fileSizeInByte": 2132,
    "mimeType": "image/jpeg"
  },
  ...
}
```

## Passing Complex JSON Bodies

Some endpoints take deeply nested request bodies (`bulk-assets`, `update-metadata`, etc.). For these, you can pass a JSON string to the `--root` flag instead of typed flags:

```bash
immich-rest-cli Albums add-assets-to-album \
  --id <album-id> \
  --root '{"ids": ["asset-1", "asset-2", "asset-3"]}'
```

Simple endpoints (like `Albums create`, `Assets upload`) take typed flags directly.

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
