---
title: "Turn an OpenAPI Spec Into a CLI People Can Actually Use"
description: "OpenAPI specs are not only for SDKs and docs. They can generate human-facing Python CLIs with typed flags, auth, table output, and nested request bodies flattened into command options."
tags: ["openapi", "python", "cli", "fastapi", "developer-tools"]
canonical_url: "https://github.com/shivaam/openapi-cli-gen"
---

# Turn an OpenAPI Spec Into a CLI People Can Actually Use

Most teams already have more API structure than they use.

If you have a FastAPI app, a Swagger spec, or any OpenAPI 3.x document, the spec
already knows your paths, methods, query parameters, path parameters, request
bodies, auth schemes, enums, and validation rules.

And yet, a lot of internal API workflows still end up as copied `curl` commands:

```bash
curl -X POST "$API_URL/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com","address":{"city":"NYC","state":"NY"}}'
```

That works, but it is not a great interface.

It is easy to mistype. It is hard to discover. It asks humans to write JSON even
when the schema already knows the fields. It also tends to sprawl across
runbooks, Slack messages, CI jobs, and one-off scripts.

I built [`openapi-cli-gen`](https://github.com/shivaam/openapi-cli-gen) to
explore a narrower idea:

> What if an OpenAPI spec could become a human-facing command line app?

## The Basic Idea

Instead of making users paste JSON:

```bash
curl -X POST /api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","address":{"city":"NYC","state":"NY"}}'
```

generate commands like this:

```bash
mycli users create \
  --name Jane \
  --address.city NYC \
  --address.state NY
```

The OpenAPI spec provides the structure. The generated CLI exposes that
structure as command groups, options, environment variables, and output formats.

## Why Not Just Use OpenAPI Generator?

OpenAPI Generator is excellent when you need SDKs, server stubs, models, or
language-specific client libraries.

That is not the same job.

`openapi-cli-gen` is aimed at a smaller workflow:

- give support teams repeatable commands;
- give ops teams admin tools;
- give QA teams setup and cleanup commands;
- give API maintainers a quick internal CLI;
- give users a scriptable wrapper around a REST API.

The distinction is:

```text
SDK generator: produce code developers import.
CLI generator: produce commands humans and scripts run.
```

Both can be useful. They just serve different moments.

## Proof: Generated CLIs From Real APIs

This is not only a design sketch. The generator has already been used to create
standalone CLI wrappers for real APIs:

- [OpenAI REST CLI](https://github.com/shivaam/openai-rest-cli): chat,
  embeddings, files, vector stores, batch, fine-tuning, images, audio, and more.
- [Qdrant REST CLI](https://github.com/shivaam/qdrant-rest-cli): collections,
  points, search, snapshots, and vector database operations.
- [Meilisearch REST CLI](https://github.com/shivaam/meilisearch-rest-cli):
  indexes, documents, search, settings, tasks, and API keys.
- [Typesense REST CLI](https://github.com/shivaam/typesense-rest-cli):
  collections, documents, search, aliases, keys, analytics, and conversations.
- [AdGuard Home CLI](https://github.com/shivaam/adguard-home-cli): filtering,
  clients, DHCP, rewrite rules, TLS, stats, and admin operations.
- [Immich REST CLI](https://github.com/shivaam/immich-rest-cli): assets,
  albums, libraries, users, search, tags, server config, and upload workflows.
- [Open Wearables REST CLI](https://github.com/shivaam/open-wearables-rest-cli):
  provider discovery, user sync/debug workflows, summaries, timeseries, and
  webhooks.
- [NeoDB REST CLI](https://github.com/shivaam/neodb-rest-cli): catalog search,
  shelf, collection, review, tag, and personal data workflows.
- [RustMailer REST CLI](https://github.com/shivaam/rustmailer-rest-cli):
  self-hosted email operator workflows across accounts, mailboxes, messages,
  hooks, and system endpoints.

That matters because the value is not just "can we generate code?" The value is
whether the generated surface can become a useful package someone can install,
inspect, and script.

## FastAPI Is A Natural Fit

FastAPI publishes an OpenAPI spec at `/openapi.json` by default.

That means a running FastAPI app can become a CLI without adding a separate API
description file:

```bash
openapi-cli-gen generate \
  --spec http://localhost:8000/openapi.json \
  --name internal-admin
```

Then:

```bash
cd internal-admin
pip install -e .
internal-admin --help
```

For internal tools, this can be enough to turn an API into something support,
ops, and QA can actually use.

## Nested Request Bodies Are The Pain Point

The easy part of an API CLI is path and query parameters.

The annoying part is request bodies.

FastAPI and Pydantic apps often use nested models:

```python
from pydantic import BaseModel


class Address(BaseModel):
    city: str
    state: str


class UserCreate(BaseModel):
    name: str
    email: str
    address: Address
```

The generated command can expose nested fields as dot flags:

```bash
internal-admin users create \
  --name Jane \
  --email jane@example.com \
  --address.city NYC \
  --address.state NY
```

For complex cases, JSON fallback is still available:

```bash
internal-admin users create \
  --address '{"city":"NYC","state":"NY"}'
```

That combination is important. Simple cases should feel simple. Complex cases
should still be possible.

## Runtime Mode vs Generated Packages

Sometimes you just want to try a spec:

```bash
openapi-cli-gen run \
  --spec https://catfact.ninja/docs \
  --base-url https://catfact.ninja \
  facts get-random
```

Sometimes you want a real package:

```bash
openapi-cli-gen generate \
  --spec https://api.example.com/openapi.json \
  --name example-cli
```

The generated package can be installed locally or shipped to users:

```bash
cd example-cli
pip install -e .
example-cli --help
```

## Where This Helps

Generated CLIs seem most useful for APIs with repeated operational workflows:

- internal admin APIs;
- FastAPI services;
- self-hosted apps;
- search and vector databases;
- import/export tools;
- media libraries;
- provider sync/debug APIs;
- QA and smoke-test endpoints.

The wrapper does not need to replace an SDK. It gives people a terminal surface
when a terminal surface is the right shape.

## The Tradeoff

Generated CLIs inherit the shape of the OpenAPI spec.

If the spec has clean tags and operation IDs, commands can feel good quickly. If
the spec has long generated operation IDs, the commands may need wrapper-level
aliases for the most common workflows.

That is still a useful starting point:

1. generate the full API surface;
2. verify real commands;
3. add aliases only where humans actually need them.

## Try It

Install:

```bash
pipx install openapi-cli-gen
```

Inspect a spec:

```bash
openapi-cli-gen inspect \
  --spec https://petstore3.swagger.io/api/v3/openapi.json
```

Generate a CLI:

```bash
openapi-cli-gen generate \
  --spec https://api.example.com/openapi.json \
  --name mycli
```

Project:

<https://github.com/shivaam/openapi-cli-gen>

I am especially interested in real OpenAPI specs that make generated CLIs
awkward: unusual auth, nested bodies, arrays of objects, multipart uploads,
unions, or very large schemas. Those are the cases that make the tool better.
