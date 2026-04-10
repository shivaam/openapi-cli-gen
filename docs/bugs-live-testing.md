# Bugs from Live API Testing (v0.0.9)

Comprehensive live test results against real APIs. Tracks what works and what doesn't.

## Summary

| API | Commands tested | Pass | Fail | Notes |
|---|---|---|---|---|
| Apache Airflow 3.2.0 | 27 | 26 | 1 | Config 403 (perms, not our bug) |
| OpenAI | 10 | 8 | 2 | Chat/Completions allOf, Assistants needs beta header |
| Qdrant | 5 | 5 | 0 | Create/list/get/delete/search all work |
| Meilisearch | 6 | 6 | 0 | Health/version/indexes/tasks/stats |
| Petstore | 4 | 1 | 3 | Their server returns 500s |
| Typesense | 0 | 0 | 1 | Model build fails with FieldInfo error |
| Cat Fact | 3 | 3 | 0 | Random fact, breeds, version |
| AdGuard Home | - | - | - | Not tested (needs web setup) |

## Open Bugs

### BUG-A: allOf composition not handled (CRITICAL)

**Impact:** Any request body schema that uses `allOf` to compose fields results in an empty command with no flags.

**Examples:**
- OpenAI `Chat create-completion` — body uses `allOf: [$ref: CreateModelResponseProperties, { properties: { messages, model, ... } }]`
- Many modern APIs use this pattern for inheritance

**Symptom:**
```bash
$ openapi-cli-gen run --spec <OpenAI> Chat create-completion --help
usage: openapi-cli-gen [-h] [--output-format str]
options:
  -h, --help
  --output-format
```

No `--messages`, `--model`, `--temperature` etc. because our model builder walks `properties` but doesn't recurse into `allOf`.

**Fix options:**
1. Add `allOf` handling to `_property_to_field` in `engine/models.py` — recursively merge properties from each `allOf` item
2. Use `datamodel-code-generator` for URL specs too (we already do this for local files) — but see BUG-B

**Priority:** CRITICAL — blocks all chat/completion APIs (the AI category)

---

### BUG-B: datamodel-code-generator fails on OpenAI spec (discriminated unions)

**Impact:** When we try to use datamodel-code-generator for URL specs (to handle `allOf`), OpenAI's spec fails during pydantic model instantiation.

**Error:**
```
InputItem(RootModel[EasyInputMessage | InputMessage | OutputMessage | ...])
    root: Annotated[..., Field(discriminator='type')]
# Pydantic error: some variants don't have matching 'type' literal
```

**Root cause:** OpenAI's `InputItem` uses a discriminated union with `propertyName: type`, but some union members don't expose `type` as a Literal. Pydantic's strict discriminator validation rejects this at model creation time.

**Fix options:**
1. Strip discriminator metadata from generated code before `exec()` — risky
2. Post-process the generated code to remove discriminator from problematic unions
3. Use `generate_models_from_spec` with error recovery (return partial models)
4. Report upstream to openai-openapi or datamodel-code-generator

**Priority:** HIGH — blocks full OpenAI support

---

### BUG-C: Typesense fails with `FieldInfo object is not iterable`

**Impact:** Typesense spec can't be parsed by our tool at all.

**Error:**
```
File "openapi_cli_gen/engine/builder.py", line 44, in build_cli
    registry = build_registry(endpoints, generated_models=generated_models)
TypeError: 'FieldInfo' object is not iterable
```

**Root cause:** Unknown — somewhere in our dispatch or registry building, a FieldInfo is being passed where a dict/list is expected. Likely a corner case in `exclude_from_body` or `_parse_json_strings`.

**Priority:** MEDIUM — blocks Typesense demos

---

### BUG-D: OpenAI Assistants needs beta header

**Impact:** `openai Assistants list` returns 400 because OpenAI requires `OpenAI-Beta: assistants=v2` header.

**Not our bug** — it's OpenAI's convention. But we should support custom headers per-endpoint (via extension in the spec or CLI flag).

**Fix:** Add `--header KEY=VALUE` flag to the run command for injecting custom headers.

**Priority:** LOW — workaround exists

---

## What Works Well

- **Simple CRUD**: GET/POST/PUT/PATCH/DELETE on typed schemas work great
- **Nested objects (flat properties)**: dot-notation works at all depths
- **Arrays/dicts/enums**: all handled by pydantic-settings
- **JSON string parsing**: `--vectors '{"size": 4}'` gets parsed correctly
- **Default value handling**: user-specified defaults aren't sent if they match spec default
- **Auth via env vars**: Bearer token from `{NAME}_TOKEN` works
- **Error responses**: 4xx/5xx shown cleanly with JSON formatting

## Live Tested And Working (v0.0.9)

### Airflow (live Breeze)
```bash
airflow Monitor get-health
airflow Version get
airflow DAG get-dags --limit 5
airflow DAG get-dag --dag-id example_bash_operator
airflow Pool get-pools
airflow Connection post --connection-id my-db --conn-type postgres --host db.example.com
airflow Connection patch --connection-id my-db --conn-type postgres --host new.example.com
airflow Connection delete --connection-id my-db
airflow Variable post --key my-var --value hello
airflow DagRun trigger-dag-run --dag-id example_bash_operator --logical-date 2026-04-09T12:00:00+00:00
```

### OpenAI (live)
```bash
export CLI_TOKEN=sk-...
openai Models list
openai Models retrieve --model gpt-4o
openai Embeddings create --input "Hello world" --model text-embedding-3-small --dimensions 8
openai Moderations create --input "I love puppies"
openai "Vector stores" create-vector-store --name my_store
openai Files list
openai Batch list-batches --limit 3
openai Completions create --model gpt-3.5-turbo-instruct --prompt "Python is" --max-tokens 30
openai Images create --prompt "A cat coding" --model dall-e-2 --size 256x256
```

### Qdrant (Docker local)
```bash
docker run -d -p 6333:6333 qdrant/qdrant
qdrant Service root
qdrant Service healthz
qdrant Collections get-collections
qdrant Collections create --collection-name test --vectors '{"size": 4, "distance": "Cosine"}'
qdrant Collections get-collection --collection-name test
qdrant Collections delete --collection-name test
```

### Meilisearch (Docker local)
```bash
docker run -d -p 7700:7700 getmeili/meilisearch
meili Health get
meili Version get
meili Indexes list
meili Indexes create-index --uid movies --primary-key id
meili Stats get
meili Tasks get-tasks --limit 3
```
