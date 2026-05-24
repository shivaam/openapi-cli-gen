# CLAUDE.md

## What this project does

`openapi-cli-gen` takes any OpenAPI 3.x spec and generates a typed Python CLI where nested request bodies become flat `--flags`. It works as a library (`build_cli()`), a runtime tool (`run`), or a code generator (`generate`).

## Quick reference

```bash
# Run tests
.venv/bin/python -m pytest tests/ -q

# Install in dev mode
uv pip install -e . --python .venv/bin/python

# Regenerate all 6 wrapper CLIs (reads wrappers/manifest.yaml)
.venv/bin/python scripts/regenerate.py

# Regenerate + publish to PyPI + push to GitHub repos
.venv/bin/python scripts/regenerate.py --publish --push

# Regenerate one wrapper
.venv/bin/python scripts/regenerate.py --only qdrant-rest-cli

# Dry run (show what would happen)
.venv/bin/python scripts/regenerate.py --dry-run
```

## Architecture

```
spec/loader.py      → load OpenAPI spec (file or URL), resolve $refs
spec/parser.py      → extract EndpointInfo list from resolved spec
engine/models.py    → generate Pydantic models via datamodel-code-generator (disk cached)
engine/registry.py  → group commands by tag, attach models
engine/builder.py   → build_cli() / build_command_group() — the public API
engine/dispatch.py  → manual CLI dispatch (group → command → execute)
engine/auth.py      → bearer, api-key, basic auth from env vars
output/formatter.py → json/yaml/table/raw output
codegen/generator.py → generate installable package from spec (Jinja2 templates)
cli.py              → typer CLI: generate, run, inspect commands
```

## Wrapper CLIs

Six pre-built CLIs generated from this tool, each in its own GitHub repo and on PyPI:

| Name | Repo | Spec source |
|------|------|-------------|
| openai-rest-cli | shivaam/openai-rest-cli | openai/openai-openapi |
| meilisearch-rest-cli | shivaam/meilisearch-rest-cli | meilisearch/open-api |
| adguard-home-cli | shivaam/adguard-home-cli | AdguardTeam/AdGuardHome |
| immich-rest-cli | shivaam/immich-rest-cli | immich-app/immich |
| qdrant-rest-cli | shivaam/qdrant-rest-cli | qdrant/qdrant |
| typesense-rest-cli | shivaam/typesense-rest-cli | typesense/typesense-api-spec |

All config lives in `wrappers/manifest.yaml` — spec URLs, base URLs, versions, repo names. Hand-written READMEs live in `wrappers/<name>/README.md` and get copied into generated packages automatically.

**To update all wrappers after a new release:**
1. Bump version in `pyproject.toml` + `src/openapi_cli_gen/__init__.py`
2. Publish `openapi-cli-gen` to PyPI
3. Bump `version` field in `wrappers/manifest.yaml` for each wrapper
4. Run `python scripts/regenerate.py --publish --push`

## Versioning

- `openapi-cli-gen` version: `pyproject.toml` and `src/openapi_cli_gen/__init__.py` (keep in sync)
- Wrapper versions: `wrappers/manifest.yaml` → `version` field per wrapper
- Generated packages pin `openapi-cli-gen>={current_version}`
- PyPI doesn't allow re-uploading the same version — always bump before publishing

## Publishing

PyPI token is in `~/.pypirc`. Build + upload:
```bash
python -m build && python -m twine upload dist/*
```

## Testing

- Unit tests: `tests/` (50 tests, ~1s)
- Live regression: `experiments/regression_test.py` (needs running API instances)
- Test spec: `tests/conftest.py` has a minimal OpenAPI spec fixture

## Key conventions

- Python package uses underscores (`openapi_cli_gen`), CLI/PyPI names use dashes (`openapi-cli-gen`)
- Generated CLIs read auth from `{PREFIX}_TOKEN`, `{PREFIX}_API_KEY`, `{PREFIX}_USERNAME`/`{PREFIX}_PASSWORD` env vars
- SSL config via `{PREFIX}_VERIFY_SSL`, `{PREFIX}_CA_CERT`, `{PREFIX}_CLIENT_CERT`, `{PREFIX}_CLIENT_KEY`
- `--root` flag on every POST/PUT/PATCH command accepts raw JSON, bypassing typed flags
- Model generation is disk-cached in `~/.cache/openapi-cli-gen/models/`
