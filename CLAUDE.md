# CLAUDE.md

Generates typed Python CLIs from OpenAPI 3.x specs. Nested request bodies become flat `--flags`.

## Commands

```bash
.venv/bin/python -m pytest tests/ -q              # run tests (50, ~1s)
uv pip install -e . --python .venv/bin/python      # dev install
.venv/bin/python scripts/regenerate.py             # regenerate all wrapper CLIs
.venv/bin/python scripts/regenerate.py --publish --push  # + PyPI + GitHub
.venv/bin/python scripts/regenerate.py --only qdrant-rest-cli  # single wrapper
```

## Architecture

```
spec/loader.py       → load spec (file/URL), resolve $refs
spec/parser.py       → extract endpoints from spec
engine/models.py     → Pydantic models via datamodel-code-generator (disk cached in ~/.cache/openapi-cli-gen/)
engine/builder.py    → build_cli() / build_command_group() public API
engine/dispatch.py   → CLI dispatch (group → command → HTTP call)
engine/auth.py       → bearer, api-key, basic auth
codegen/generator.py → generate installable package (Jinja2 templates)
cli.py               → typer CLI: generate, run, inspect
```

## Wrappers

Six CLIs, each in its own repo/PyPI package. Config in `wrappers/manifest.yaml`.

| Name | Repo |
|------|------|
| openai-rest-cli | shivaam/openai-rest-cli |
| meilisearch-rest-cli | shivaam/meilisearch-rest-cli |
| adguard-home-cli | shivaam/adguard-home-cli |
| immich-rest-cli | shivaam/immich-rest-cli |
| qdrant-rest-cli | shivaam/qdrant-rest-cli |
| typesense-rest-cli | shivaam/typesense-rest-cli |

Hand-written READMEs in `wrappers/<name>/README.md` are copied into generated packages.

## Releasing

1. Bump version in both `pyproject.toml` and `src/openapi_cli_gen/__init__.py`
2. `python -m build && python -m twine upload dist/*`
3. Bump `version` in `wrappers/manifest.yaml` (PyPI rejects duplicate versions)
4. `python scripts/regenerate.py --publish --push`

## Conventions

- Dashes for CLI/PyPI names, underscores for Python packages
- Auth env vars: `{PREFIX}_TOKEN`, `{PREFIX}_API_KEY`, `{PREFIX}_USERNAME`/`{PREFIX}_PASSWORD`
- SSL env vars: `{PREFIX}_VERIFY_SSL`, `{PREFIX}_CA_CERT`, `{PREFIX}_CLIENT_CERT`, `{PREFIX}_CLIENT_KEY`
- `--root` flag on POST/PUT/PATCH accepts raw JSON, bypassing typed flags
