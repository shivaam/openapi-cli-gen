# adguard-home-cli

**A full-coverage CLI for [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome).** Every endpoint in the AdGuard Home OpenAPI spec, exposed as a typed shell command. Generated from [AdGuard Home's official OpenAPI spec](https://github.com/AdguardTeam/AdGuardHome/blob/master/openapi/openapi.yaml) using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

A CLI for AdGuard Home has been one of the [most-requested community features](https://github.com/AdguardTeam/AdGuardHome/issues/1147) — with [dedicated](https://github.com/AdguardTeam/AdGuardHome/issues/1428) [feature](https://github.com/AdguardTeam/AdGuardHome/issues/7917) requests asking for scripting, Infrastructure-as-Code, and automated provisioning. The project maintainers have focused on the web UI and DNS engine; there's no official CLI.

This fills the gap: every HTTP API endpoint in AdGuard Home becomes a shell command with typed flags. Useful for:

- **Ansible / homelab provisioning** — set filter URLs, block lists, TLS config from a playbook
- **Sync across instances** — dump config from one AdGuard Home, apply to another
- **Monitoring scripts** — query protection state, blocked counts, query logs
- **Scheduled blocked-services toggles** — turn Netflix on for movie night via cron
- **Bulk rule management** — add / remove user rules programmatically

## Install

```bash
pipx install adguard-home-cli

# Or with uv
uv tool install adguard-home-cli
```

## Setup

Point it at your AdGuard Home instance. **Note:** the REST API is served under `/control`:

```bash
export ADGUARD_HOME_CLI_BASE_URL=http://your-adguard-host:3000/control
```

### Authentication

AdGuard Home uses HTTP Basic auth with your admin credentials:

```bash
export ADGUARD_HOME_CLI_USERNAME=admin
export ADGUARD_HOME_CLI_PASSWORD=your-password
```

The CLI automatically sends the `Authorization: Basic ...` header on every request.

## Quick Start

```bash
# Server status (version, DNS addresses, running state)
adguard-home-cli global status

# Stats summary
adguard-home-cli stats info
adguard-home-cli stats stats

# Filter status (which lists are enabled, update intervals)
adguard-home-cli filtering status

# Add a new blocklist URL
adguard-home-cli filtering add-url \
  --name "OISD Full" \
  --url "https://big.oisd.nl/" \
  --whitelist false

# Refresh all filters
adguard-home-cli filtering refresh

# Set user-defined block rules
adguard-home-cli filtering set-rules --rules '["||example.com^", "||tracker.io^"]'

# Look up a host (debugging)
adguard-home-cli filtering check-host --name doubleclick.net

# Client management
adguard-home-cli clients status
adguard-home-cli clients find

# Safe browsing / parental controls / safe search
adguard-home-cli safebrowsing status
adguard-home-cli parental status
adguard-home-cli safesearch status

# Blocked services (one-off block of Netflix, YouTube, etc.)
adguard-home-cli blocked_services list
adguard-home-cli blocked_services set --root '{"ids": ["netflix", "tiktok"]}'

# Query log
adguard-home-cli log query --limit 50

# DNS rewrites (local DNS entries)
adguard-home-cli rewrite list
adguard-home-cli rewrite add --domain home.lan --answer 192.168.1.10
```

## Discover All Commands

```bash
# Top-level groups
adguard-home-cli --help

# Commands in a group
adguard-home-cli filtering --help

# Flags for a specific command
adguard-home-cli filtering add-url --help
```

## Output Formats

Every command accepts `--output-format`:

```bash
adguard-home-cli global status --output-format table
adguard-home-cli stats info --output-format yaml
adguard-home-cli filtering status --output-format raw
```

## Command Groups

| Group | What it covers |
|---|---|
| `global` | Server status, DNS config, protection toggle, profile, updates |
| `install` | Initial setup wizard (address discovery, configure, check-config) |
| `filtering` | Block lists, allow lists, user rules, host lookup |
| `clients` | Per-client access lists and settings |
| `dhcp` | DHCP server + static leases |
| `log` | Query log config + search |
| `stats` | Query statistics + config |
| `blocked_services` | Time-scheduled service blocking (Netflix, TikTok, etc.) |
| `safebrowsing` | Google Safe Browsing toggle |
| `parental` | Parental control toggle |
| `safesearch` | Safe search enforcement |
| `rewrite` | Local DNS rewrites (map domains to IPs) |
| `tls` | HTTPS / DNS-over-TLS / DNS-over-HTTPS config |
| `mobileconfig` | Generate iOS/macOS mobile config profiles |
| `i18n` | UI language |

## Real Example: Bootstrap a New AdGuard Home Instance

```bash
#!/usr/bin/env bash
set -e

export ADGUARD_HOME_CLI_BASE_URL=http://new-adguard:3000/control
export ADGUARD_HOME_CLI_USERNAME=admin
export ADGUARD_HOME_CLI_PASSWORD=$ADMIN_PASSWORD

# Add block lists
adguard-home-cli filtering add-url --name "OISD"        --url "https://big.oisd.nl/"            --whitelist false
adguard-home-cli filtering add-url --name "StevenBlack" --url "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts" --whitelist false

# Refresh
adguard-home-cli filtering refresh

# Add local rewrites
adguard-home-cli rewrite add --domain router.lan --answer 192.168.1.1
adguard-home-cli rewrite add --domain nas.lan    --answer 192.168.1.20

# Enable safe browsing + parental
adguard-home-cli safebrowsing enable
adguard-home-cli parental    enable

# Verify
adguard-home-cli global status --output-format json | jq .protection_enabled
```

## How It Works

This package is a thin wrapper:
- Embeds the AdGuard Home OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime

Since it's spec-driven, new AdGuard Home endpoints show up automatically on regeneration — no manual wrapping.

## License

MIT. Not affiliated with AdGuard — this is an unofficial community CLI built on top of their public OpenAPI spec.
