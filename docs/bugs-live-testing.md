# Bugs from Live API Testing

Live test results across real APIs. Updated as we find and fix issues.

## Current Status (v0.0.11)

**Regression suite: 22/22 passing** (run `.venv/bin/python experiments/regression_test.py`)

| API | Pass | Total | Last tested |
|---|---|---|---|
| Qdrant (Docker) | 7 | 7 | v0.0.11 |
| Meilisearch (Docker) | 7 | 7 | v0.0.11 |
| OpenAI | 8 | 8 | v0.0.11 |
| Apache Airflow 3.2.0 | 26 | 27 | v0.0.9 (1 is auth permissions) |

## Key Fixes Log

### v0.0.11 — big round of fixes

**BUG-A: allOf body schemas missing all fields (FIXED)**
- Symptom: OpenAI `Chat create-completion` showed no flags
- Root cause: Our simple model builder didn't walk `allOf` composition. After jsonref resolved the refs, the original schema name was lost.
- Fix: Added `load_raw_spec()` + `extract_body_schema_names()` to track $ref names before resolution. Parser now stores `body_ref_name` alongside schema. Registry looks up generated models by ref name.

**BUG-B: OpenAI discriminator unions break pydantic model loading (FIXED)**
- Symptom: `TypeError: Value 'message' for discriminator 'type' mapped to multiple choices`
- Root cause: OpenAI spec has ambiguous discriminated unions (two variants with `type: "message"`). Pydantic rejects at model creation.
- Fix: Post-process generated code to strip `discriminator='type'` from Field() calls. Pydantic falls back to trying each variant in order — good enough for CLI use.

**BUG-E: Recursive types broken by stripping future annotations (FIXED, regression)**
- Symptom: `NameError: name 'ProgressTree' is not defined` for self-referencing types
- Root cause: I stripped `from __future__ import annotations` to help pydantic-settings resolve types, but this broke recursive types.
- Fix: Keep future annotations, call `model.model_rebuild()` on each class after loading with module namespace.

**BUG-F: Complex union types can't be flag-ified (FIXED via fallback)**
- Symptom: `Input should be a valid dictionary or instance of VectorParams`
- Root cause: Generated models have exact types like `VectorParams | Record`. pydantic-settings can't build CLI flags for these.
- Fix: Detect complex types (multi-BaseModel unions, lists of BaseModels, RootModels, BaseModels with nested complex types) and fall back to `str | None`. User passes JSON string which we parse before sending.

**BUG-G: CamelCase aliases become CLI flags (FIXED)**
- Symptom: Meilisearch showed `--primaryKey` instead of `--primary-key`
- Root cause: `datamodel-code-generator --snake-case-field` renames fields to snake_case but sets `alias=original_name`. pydantic-settings uses the alias for CLI flags.
- Fix: Strip `alias` from FieldInfo, keep `serialization_alias` so JSON serialization uses the original name. Path/query params also snake_cased with alias preserving original for URL substitution.

**BUG-H: Defaults with wrong type break validation (FIXED)**
- Symptom: `Input should be a valid string [type=string_type, input_value=True]`
- Root cause: When falling back to str for complex types, we kept the original default (e.g., `True` bool). Pydantic rejected bool as string.
- Fix: Drop the default entirely when falling back to str.

### Earlier fixes (v0.0.6–v0.0.10)

- **v0.0.10**: Enabled datamodel-code-generator for URL specs (downloads to cache)
- **v0.0.9**: 5min httpx timeout for long-running ops (DALL-E)
- **v0.0.9**: Drop defaults that equal spec default (enum-aware)
- **v0.0.6**: Parse JSON strings in body fields (`--vectors '{"size":4}'`)
- **v0.0.5**: `generate` command downloads URL specs
- **v0.0.4**: Passthrough flags in run command (Typer context_settings)
- **v0.0.3**: Add `--base-url` to run command
- **v0.0.2**: Move typer + datamodel-code-generator to main deps

## Open Issues

### BUG-C: Typesense `FieldInfo object is not iterable`
- **Status**: Still blocked
- **Priority**: Medium
- **Impact**: Typesense spec fails at build_registry step

### BUG-I: pydantic-settings `BooleanOptionalAction nargs` error on very complex specs
- **Status**: Workarounds apply (some fields fall back to str), but certain edge cases still hit it
- **Priority**: Low (affects only deeply nested booleans in OpenAI-scale specs)
- **Upstream**: Should file with pydantic-settings

### BUG-D: OpenAI Assistants API needs `OpenAI-Beta` header
- **Status**: Workaround needed — add `--header KEY=VALUE` flag
- **Priority**: Low

## Live Tested And Working (v0.0.11)

### Qdrant (Docker localhost:6333)
```bash
qdrant Service root
qdrant Service healthz
qdrant Collections get-collections
qdrant Collections create --collection-name test --vectors '{"size": 4, "distance": "Cosine"}'
qdrant Collections get-collection --collection-name test
qdrant Collections exists --collection-name test
qdrant Collections delete --collection-name test
```

### Meilisearch (Docker localhost:7700)
```bash
meili Health get
meili Version get
meili Indexes list
meili Indexes create-index --uid my_index --primary-key id
meili Stats get
meili Tasks get-tasks
meili Indexes delete-index --index-uid my_index
```

### OpenAI (live API)
```bash
export CLI_TOKEN=sk-...
openai Models list
openai Models retrieve --model gpt-4o
openai Embeddings create --input "Hello" --model text-embedding-3-small --dimensions 4
openai Moderations create --input "I love cats"
openai Completions create --model gpt-3.5-turbo-instruct --prompt "Python is" --max-tokens 10
openai Chat create-completion --model gpt-4o-mini --messages '[{"role":"user","content":"Hi"}]'
openai Files list
openai "Vector stores" list-vector-stores
```

### Apache Airflow (live Breeze)
```bash
airflow Monitor get-health
airflow Version get
airflow DAG get-dags --limit 5
airflow Pool get-pools
airflow Connection post --connection-id my-db --conn-type postgres --host db.example.com
airflow Connection patch --connection-id my-db --conn-type postgres --host new.example.com
airflow Connection delete --connection-id my-db
airflow DagRun trigger-dag-run --dag-id example_bash_operator --logical-date 2026-04-09T12:00:00+00:00
```

## Regression Test

Run the full suite after any change:

```bash
export CLI_TOKEN=sk-...
.venv/bin/python experiments/regression_test.py
```

Requires:
- Qdrant: `docker run -d -p 6333:6333 qdrant/qdrant`
- Meilisearch: `docker run -d -p 7700:7700 getmeili/meilisearch`
- OpenAI: `CLI_TOKEN` env var
