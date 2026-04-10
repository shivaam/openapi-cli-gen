# Supported APIs — What Works Today

Every command on this page has been **live tested** against the real API. Run the regression suite to verify: `.venv/bin/python experiments/regression_test.py`

---

## OpenAI

**Spec:** `https://raw.githubusercontent.com/openai/openai-openapi/2025-03-21/openapi.yaml`
**Auth:** `export CLI_TOKEN=sk-...`
**Base URL:** from spec (no `--base-url` needed)

```bash
SPEC=https://raw.githubusercontent.com/openai/openai-openapi/2025-03-21/openapi.yaml

# List all models
openapi-cli-gen run --spec $SPEC Models list

# Get a specific model
openapi-cli-gen run --spec $SPEC Models retrieve --model gpt-4o-mini

# Chat completion (GPT-4o-mini)
openapi-cli-gen run --spec $SPEC Chat create-completion \
  --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Hello, how are you?"}]'

# Legacy text completion (GPT-3.5-turbo-instruct)
openapi-cli-gen run --spec $SPEC Completions create \
  --model gpt-3.5-turbo-instruct \
  --prompt "Python is" \
  --max-tokens 30

# Generate an embedding
openapi-cli-gen run --spec $SPEC Embeddings create \
  --input "Hello world" \
  --model text-embedding-3-small \
  --dimensions 8

# Classify content (moderation)
openapi-cli-gen run --spec $SPEC Moderations create --input "I love puppies"

# Generate an image with DALL-E
openapi-cli-gen run --spec $SPEC Images create \
  --prompt "A cat coding on a laptop, digital art" \
  --model dall-e-2 \
  --size 256x256

# List files
openapi-cli-gen run --spec $SPEC Files list

# Create a vector store
openapi-cli-gen run --spec $SPEC "Vector stores" create-vector-store --name my_store

# List vector stores
openapi-cli-gen run --spec $SPEC "Vector stores" list-vector-stores
```

**Status:** 8/8 regression tests pass.
**Known limitations:** Assistants API requires `OpenAI-Beta` header (not yet supported). Audit Logs require admin key.

---

## Qdrant (Vector DB)

**Spec:** `https://raw.githubusercontent.com/qdrant/qdrant/master/docs/redoc/master/openapi.json`
**Setup:** `docker run -d -p 6333:6333 qdrant/qdrant`
**Base URL:** `http://localhost:6333`

```bash
SPEC=https://raw.githubusercontent.com/qdrant/qdrant/master/docs/redoc/master/openapi.json
URL=http://localhost:6333

# Service info
openapi-cli-gen run --spec $SPEC --base-url $URL Service root
openapi-cli-gen run --spec $SPEC --base-url $URL Service healthz

# Create a collection (pass nested config as JSON)
openapi-cli-gen run --spec $SPEC --base-url $URL Collections create \
  --collection-name pets \
  --vectors '{"size": 4, "distance": "Cosine"}'

# List collections
openapi-cli-gen run --spec $SPEC --base-url $URL Collections get-collections

# Get collection info
openapi-cli-gen run --spec $SPEC --base-url $URL Collections get-collection --collection-name pets

# Upsert vectors (RootModel body — unwrapped automatically)
openapi-cli-gen run --spec $SPEC --base-url $URL Points upsert \
  --collection-name pets \
  --root '{"points": [{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"name": "Buddy"}}, {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8], "payload": {"name": "Luna"}}]}'

# Count points
openapi-cli-gen run --spec $SPEC --base-url $URL Points count --collection-name pets

# Get a specific point
openapi-cli-gen run --spec $SPEC --base-url $URL Points get-point --collection-name pets --id 1

# Scroll through points
openapi-cli-gen run --spec $SPEC --base-url $URL Points scroll --collection-name pets --limit 10

# Semantic search (nearest neighbors)
openapi-cli-gen run --spec $SPEC --base-url $URL Search query-points \
  --collection-name pets \
  --query '[0.1, 0.2, 0.3, 0.4]' \
  --limit 5

# Delete collection
openapi-cli-gen run --spec $SPEC --base-url $URL Collections delete --collection-name pets
```

**Status:** 14/14 regression tests pass (7 Collections + 7 Points).

---

## Meilisearch

**Spec:** `https://raw.githubusercontent.com/meilisearch/open-api/main/open-api.json`
**Setup:** `docker run -d -p 7700:7700 getmeili/meilisearch`
**Base URL:** `http://localhost:7700`

```bash
SPEC=https://raw.githubusercontent.com/meilisearch/open-api/main/open-api.json
URL=http://localhost:7700

# Health check
openapi-cli-gen run --spec $SPEC --base-url $URL Health get

# Server version
openapi-cli-gen run --spec $SPEC --base-url $URL Version get

# List indexes
openapi-cli-gen run --spec $SPEC --base-url $URL Indexes list

# Create an index
openapi-cli-gen run --spec $SPEC --base-url $URL Indexes create-index --uid movies --primary-key id

# Get stats
openapi-cli-gen run --spec $SPEC --base-url $URL Stats get

# List tasks
openapi-cli-gen run --spec $SPEC --base-url $URL Tasks get-tasks

# Delete an index
openapi-cli-gen run --spec $SPEC --base-url $URL Indexes delete-index --index-uid movies
```

**Status:** 7/7 regression tests pass.

---

## Typesense (Search)

**Spec:** `https://raw.githubusercontent.com/typesense/typesense-api-spec/master/openapi.yml`
**Setup:** `docker run -d -p 8108:8108 typesense/typesense:27.1 --data-dir /tmp --api-key=xyz --enable-cors`
**Base URL:** `http://localhost:8108`

```bash
SPEC=https://raw.githubusercontent.com/typesense/typesense-api-spec/master/openapi.yml
URL=http://localhost:8108

# Health check (no auth needed)
openapi-cli-gen run --spec $SPEC --base-url $URL health health
```

**Status:** Health passes (1/1). Full CRUD not yet in regression but spec parses cleanly with 15 command groups.

---

## GitHub Public API

**Spec:** `https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json`
**Auth:** None required for public endpoints (rate-limited). For authenticated: `export CLI_TOKEN=ghp_...`
**Base URL:** `https://api.github.com`

```bash
SPEC=https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json
URL=https://api.github.com

# GitHub's "zen" one-liner
openapi-cli-gen run --spec $SPEC --base-url $URL meta meta/get-zen

# Get the Octocat
openapi-cli-gen run --spec $SPEC --base-url $URL meta meta/get-octocat

# API root with all endpoint URLs
openapi-cli-gen run --spec $SPEC --base-url $URL meta meta/root

# Current rate limit
openapi-cli-gen run --spec $SPEC --base-url $URL rate-limit rate-limit/get

# Get a user by username
openapi-cli-gen run --spec $SPEC --base-url $URL users users/get-by-username --username torvalds

# Get a license
openapi-cli-gen run --spec $SPEC --base-url $URL licenses licenses/get --license mit
```

**Status:** 6/6 regression tests pass.

---

## Apache Airflow 3.2.0

**Spec:** Local file (bundled with Airflow): `airflow/airflow-core/src/airflow/api_fastapi/core_api/openapi/v2-rest-api-generated.yaml`
**Setup:** Run Airflow via Breeze (`breeze start-airflow`) on port 28080
**Auth:** Get token via `/auth/token` endpoint, export as `AIRFLOW_TOKEN`
**Base URL:** `http://localhost:28080`

```bash
SPEC=/path/to/v2-rest-api-generated.yaml
URL=http://localhost:28080
export AIRFLOW_TOKEN=<your-token>

# Health + version
openapi-cli-gen run --spec $SPEC --base-url $URL Monitor get-health
openapi-cli-gen run --spec $SPEC --base-url $URL Version get

# List DAGs
openapi-cli-gen run --spec $SPEC --base-url $URL DAG get-dags --limit 5

# Trigger a DAG run (with datetime param)
openapi-cli-gen run --spec $SPEC --base-url $URL DagRun trigger-dag-run \
  --dag-id example_bash_operator \
  --logical-date 2026-04-09T12:00:00+00:00

# Create a connection
openapi-cli-gen run --spec $SPEC --base-url $URL Connection post \
  --connection-id my-db \
  --conn-type postgres \
  --host db.example.com \
  --port 5432

# Update a connection
openapi-cli-gen run --spec $SPEC --base-url $URL Connection patch \
  --connection-id my-db \
  --conn-type postgres \
  --host new.example.com

# Delete a connection
openapi-cli-gen run --spec $SPEC --base-url $URL Connection delete --connection-id my-db

# Pool management
openapi-cli-gen run --spec $SPEC --base-url $URL Pool get-pools
openapi-cli-gen run --spec $SPEC --base-url $URL Pool post --name my-pool --slots 10

# Variables
openapi-cli-gen run --spec $SPEC --base-url $URL Variable post --key my-var --value hello
```

**Status:** 26/27 tested live. The 1 failure is auth permissions on Config endpoint, not a bug.

---

## Also Parsed (Not In Live Regression)

These specs parse cleanly with our tool but aren't in the live regression suite yet:

| API | Endpoints | Spec |
|---|---|---|
| Swagger Petstore | 19 | https://petstore3.swagger.io/api/v3/openapi.json |
| Redocly Museum | 8 | https://raw.githubusercontent.com/Redocly/museum-openapi-example/main/openapi.yaml |
| Open-Meteo | 1 | https://raw.githubusercontent.com/open-meteo/open-meteo/main/openapi.yml |
| Immich | 245 | https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json |
| Hetzner Cloud | 221 | https://raw.githubusercontent.com/MaximilianKoestler/hcloud-openapi/master/openapi/hcloud.json |
| Discord | 230 | https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json |

---

## Running The Regression Suite

```bash
# Prerequisites
docker run -d -p 6333:6333 qdrant/qdrant
docker run -d -p 7700:7700 getmeili/meilisearch
docker run -d -p 8108:8108 typesense/typesense:27.1 --data-dir /tmp --api-key=xyz --enable-cors
export CLI_TOKEN=sk-...  # OpenAI API key

# Run all 36 tests
cd openapi-cli-gen
.venv/bin/python experiments/regression_test.py
```

Expected output: `OVERALL: 36/36`.
