# Changelog

## v0.0.13 (2026-04-10)

**Publishing infrastructure: generate command now produces installable packages.**

### Fixed
- **BUG-L**: Package names with dashes (e.g., `qdrant-api-cli`) now work. Module directory is sanitized to `qdrant_api_cli` while keeping `qdrant-api-cli` as PyPI name and CLI binary.
- **BUG-M**: Generated CLI now accepts `--base-url` flag at generate time, and supports `{NAME}_BASE_URL` env var at runtime.

### Added
- `--base-url` flag to `generate` command for pre-configuring API endpoints
- `[tool.hatch.build.targets.wheel]` section in generated pyproject.toml for proper packaging
- Environment variable support: generated CLIs read `{NAME}_BASE_URL` automatically

### Verified end-to-end
Generated `qdrant-api-cli` package, installed with `pip install -e .`, ran live commands against Docker Qdrant:
```bash
qdrant-api-cli Service root                    # Returns version info
qdrant-api-cli Collections get-collections     # Returns real collections
```

## v0.0.12 (2026-04-10)

**35/35 regression tests passing across 6 live APIs.** Added Qdrant Points CRUD and GitHub public API to the regression suite. Typesense unblocked.

### Fixed
- **BUG-J**: RootModel body wrapper. When body is a RootModel (single `root` field), unwrap before sending. Fixes Qdrant Points upsert.
- **BUG-K**: Empty body for POST/PUT/PATCH. If endpoint declares body schema but user provided no fields, send `{}` instead of `null`. Fixes Qdrant Points count.
- **BUG-C** (previously reported): Typesense `FieldInfo object is not iterable` — automatically fixed by the v0.0.11 complex union fallback.

### Added
- Qdrant Points CRUD regression tests (7 tests): upsert, count, get, scroll, query-points, delete
- GitHub public API regression tests (6 tests): meta, zen, octocat, rate-limit, licenses, users
- Typesense to regression (manually verified, health works live)

## v0.0.11 (2026-04-10)

**22/22 regression tests passing. OpenAI Chat Completions working live.**

### Fixed
- **BUG-A**: `allOf` composition missing fields. Body schemas using `allOf: [$ref, ...]` now resolve via raw spec ref tracking. Unlocks OpenAI Chat Completions.
- **BUG-B**: OpenAI discriminator unions break pydantic. Post-process generated code to strip `discriminator='type'` from Field() calls.
- **BUG-E**: Recursive types broken. Keep `from __future__ import annotations`, call `model_rebuild()` after loading.
- **BUG-F**: Complex union types can't be flag-ified. Detect multi-BaseModel unions, lists of BaseModels, RootModels, problematic nested types. Fall back to `str | None` accepting JSON input.
- **BUG-G**: camelCase aliases leaking into CLI flags. Strip `alias`, keep `serialization_alias` for JSON output.
- **BUG-H**: Invalid defaults when falling back to str. Drop the default entirely.

### Added
- `load_raw_spec()` and `extract_body_schema_names()` to preserve $ref names before resolution
- `body_ref_name` field on EndpointInfo
- Snake-case path/query params with original name as serialization_alias
- `experiments/regression_test.py` — live API test runner

## v0.0.9 (2026-04-09)

### Fixed
- **BUG**: Spec defaults sent even when user didn't specify. Compare serialized value to serialized default (enum-aware), drop matches.
- **BUG**: 30-second timeout too short for DALL-E image generation. Bumped to 5 minutes.

## v0.0.8 — v0.0.3 (2026-04-09)

Rapid fix cycle for real-user issues:

### v0.0.6
- Parse JSON strings in body fields (`--vectors '{"size":4}'`)

### v0.0.5
- `generate` command downloads URL specs before copying

### v0.0.4
- Passthrough flags in `run` command via Typer `context_settings`

### v0.0.3
- Add `--base-url` flag to `run` command

### v0.0.2
- Move `typer` and `datamodel-code-generator` to main dependencies (were dev-only, broke `pipx install`)

## v0.0.1 (2026-04-09)

Initial PyPI release. Core features:

### Generated CLI features
- `openapi-cli-gen generate --spec <spec> --name <pkg>` — generates a pip-installable CLI package
- `openapi-cli-gen run --spec <spec> <group> <cmd>` — runtime mode, no codegen
- `openapi-cli-gen inspect --spec <spec>` — shows what would be generated

### Core engine
- Parse OpenAPI 3.0/3.1 specs from local files or URLs
- Resolve `$ref` references (local + external + circular) via jsonref
- Generate Pydantic models via datamodel-code-generator (disk cached)
- Build dynamic command tree with manual dispatch
- pydantic-settings CLI layer for nested model flattening

### API support
- All HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Path params, query params, request bodies
- Nested objects at any depth, arrays, dicts, enums, nullable fields
- Bearer token, API key, Basic auth
- JSON, YAML, table, raw output formats
