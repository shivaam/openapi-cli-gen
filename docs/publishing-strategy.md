# Publishing Pre-Built CLIs for Popular APIs

Strategy for getting openapi-cli-gen traction: publish ready-to-use CLI wrappers for popular APIs as separate PyPI packages. Each one becomes a distribution channel that leads users back to the main tool.

## The Vision

```bash
pipx install qdrant-cli
qdrant collections create --name pets --vectors '{"size": 4, "distance": "Cosine"}'

pipx install meili-cli
meili indexes list

pipx install openai-cli-gen
openai chat create-completion --model gpt-4o-mini --messages '...'
```

Each CLI is a ~10-line Python package that imports `openapi-cli-gen`, loads its embedded spec, and exposes the commands.

## Target APIs (priority order)

Ranked by CLI gap × user demand:

| # | API | Package name | Why |
|---|---|---|---|
| 1 | **Qdrant** | `qdrant-api-cli` | 60k+ GH stars, no official CLI, full CRUD works in our tool |
| 2 | **Meilisearch** | `meilisearch-api-cli` | Long-standing roadmap request for CLI, clean spec |
| 3 | **OpenAI** | `openai-api-cli` | Huge audience, legacy CLI is stale, our tool handles Chat + DALL-E |
| 4 | **Typesense** | `typesense-api-cli` | Zero official CLI, clean spec |
| 5 | **Airflow** | `airflow-rest-cli` | Alternative to airflowctl, bigger API coverage |

Names avoid collisions with existing official CLIs (`qdrant-client`, `meilisearch`, `openai`, etc.).

## Blockers Status (updated 2026-04-10)

- ✅ **BUG-L** (package name sanitization) — **FIXED in v0.0.13**
- ✅ **BUG-M** (default base URL) — **FIXED in v0.0.13**
- ⏳ BUG-N (README/metadata customization) — not fixed, manual workaround works
- ⏳ BUG-O (spec update path) — not fixed, manual regeneration works

**First pre-built CLI tested end-to-end**:

```bash
openapi-cli-gen generate --spec <qdrant-url> --name qdrant-api-cli \
  --base-url http://localhost:6333 --output /tmp/qdrant-api-cli

cd /tmp/qdrant-api-cli && pip install -e .
qdrant-api-cli Service root                       # Returns Qdrant version
qdrant-api-cli Collections get-collections        # Returns real collections
```

Ready to publish to PyPI.

## Original Blocker Details (historical)

### BUG-L: Package names with dashes break pyproject.toml (FIXED)

**Symptom:**
```bash
openapi-cli-gen generate --spec <spec> --name qdrant-cli --output ./qdrant-cli
cd qdrant-cli && pip install -e .
# × Encountered error while generating package metadata
```

**Root cause:** Generated `src/qdrant-cli/` is an invalid Python package directory (dashes not allowed). The pyproject.toml also references `qdrant-cli.cli:main` as an entry point which won't import.

**Fix required:**
1. Sanitize the `--name` for Python: `qdrant-cli` → `qdrant_cli` for the directory and module path, keep `qdrant-cli` for the PyPI name and CLI binary
2. Update `pyproject.toml` template to emit `qdrant-cli = "qdrant_cli.cli:main"`
3. Add `[tool.hatch.build.targets.wheel]` config to tell hatchling the package name

**Priority:** CRITICAL. Blocks all publishing.

### BUG-M: Generated cli.py can't set a default base_url

**Symptom:** The generated `cli.py` is:
```python
app = build_cli(
    spec=Path(__file__).parent / "spec.yaml",
    name="qdrant-cli",
)
```

If the API spec has no `servers` field (or the user needs to point at their own instance), they have no way to configure the base URL without editing the generated file.

**Fix required:**
1. Add `--default-base-url` flag to `generate` command
2. Inject it into the generated cli.py:
   ```python
   import os
   app = build_cli(
       spec=Path(__file__).parent / "spec.yaml",
       name="qdrant-cli",
       base_url=os.environ.get("QDRANT_BASE_URL", "http://localhost:6333"),
   )
   ```
3. Alternatively, pass `--base-url` through from the generated CLI invocation to the internal `build_cli`

**Priority:** HIGH. Without this, each published CLI needs manual editing to be useful.

### BUG-N: No README or description customization in generate

The generated `pyproject.toml` has:
```
description = "CLI for qdrant-cli API"
```

And no README. For PyPI publishing we need:
- Meaningful description
- README with install + usage examples
- Proper classifiers
- Keywords
- URLs (homepage, issues, source)

**Fix required:** Add `generate` flags for metadata OR a `--metadata-file` that injects into the template. Minimum viable: generate a README.md with copy-paste examples from `openapi-cli-gen inspect`.

**Priority:** MEDIUM. Can manually edit for now, but automating improves the experience.

### BUG-O: Spec URL not captured for update path

When someone installs a generated CLI, they should be able to update the spec with one command:
```bash
qdrant-cli --update-spec
```

Requires storing the original spec URL in the package metadata, then re-downloading and replacing `spec.yaml`.

**Priority:** LOW. Manual regeneration works.

## Implementation Plan

### Phase 1: Fix blockers (1-2 days)

1. Fix BUG-L (package name sanitization) — ~2 hours
2. Fix BUG-M (default base URL) — ~1 hour
3. Fix BUG-N (better metadata) — ~3 hours
4. Add tests for `generate` command that `pip install -e .` the output

### Phase 2: Publish first CLI (qdrant-api-cli)

1. Run `openapi-cli-gen generate --spec <qdrant> --name qdrant-api-cli --default-base-url http://localhost:6333`
2. Manually polish README with Qdrant-specific examples
3. Create GitHub repo `shivaam/qdrant-api-cli`
4. Upload to PyPI
5. Tweet about it

### Phase 3: Standardize and publish others

Once the process is smooth:
- `meilisearch-api-cli`
- `openai-api-cli`
- `typesense-api-cli`
- `airflow-rest-cli`

### Phase 4: Discoverability

- Submit to awesome-openapi
- Blog post: "I built CLIs for 5 APIs in 1 weekend"
- HN Show HN launch for main tool with these CLIs as exhibits

## Why Pre-Built CLIs Over Just Documenting

| | Documented examples | Published CLI packages |
|---|---|---|
| User friction | "Copy this command" | `pipx install X` |
| Discoverability | Must find our docs | PyPI search surfaces it |
| SEO | Our README | Each CLI has its own page |
| Credibility | "This tool works" | "Look, people use it to build real CLIs" |
| Maintenance | Zero | Small — regenerate on spec updates |

The overhead per CLI is ~30 minutes once the blockers are fixed. The distribution benefit is measured in thousands of potential installs.

## Example Package: qdrant-api-cli

Structure after fixes:
```
qdrant-api-cli/
├── pyproject.toml              # name = "qdrant-api-cli", package = "qdrant_api_cli"
├── README.md                   # Qdrant-specific examples
├── src/
│   └── qdrant_api_cli/
│       ├── __init__.py
│       ├── cli.py              # 10 lines: build_cli() + os.environ
│       └── spec.yaml           # Qdrant OpenAPI spec
```

Install and use:
```bash
pipx install qdrant-api-cli
qdrant-api-cli --help
qdrant-api-cli Collections get-collections
```

Under the hood it's still openapi-cli-gen — the generated package is 99% spec + 1 cli.py entry point.
