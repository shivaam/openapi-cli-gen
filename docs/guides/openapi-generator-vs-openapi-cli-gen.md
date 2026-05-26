# OpenAPI Generator vs openapi-cli-gen

OpenAPI Generator and `openapi-cli-gen` solve different problems.

OpenAPI Generator is a broad code generator. It can generate SDKs, server stubs,
models, documentation helpers, and many language-specific clients.

`openapi-cli-gen` is narrower: it generates Python command line apps from
OpenAPI specs. The goal is not to create another SDK directory. The goal is to
give humans and scripts a usable terminal interface for an API.

## Quick Comparison

| Use case | Better fit |
|---|---|
| Generate SDKs in many languages | OpenAPI Generator |
| Generate server stubs | OpenAPI Generator |
| Generate a typed Python CLI from an OpenAPI spec | `openapi-cli-gen` |
| Turn a FastAPI `/openapi.json` endpoint into an admin CLI | `openapi-cli-gen` |
| Give ops/support/QA teams commands instead of `curl` snippets | `openapi-cli-gen` |
| Publish a lightweight API wrapper installable with `pipx` | `openapi-cli-gen` |

## Choose OpenAPI Generator When

Use OpenAPI Generator when you need:

- client SDKs for several languages;
- server scaffolding;
- generated models for application code;
- mature language-specific generator templates;
- a large ecosystem with many output targets.

That is the right choice for SDK and server-code generation.

## Choose openapi-cli-gen When

Use `openapi-cli-gen` when you need:

- a command line app for an existing REST API;
- a FastAPI CLI generated from `/openapi.json`;
- a Swagger CLI generator for internal tools;
- a shell-friendly interface for support, ops, QA, or demos;
- typed parameters and request-body flags;
- a generated wrapper package that can be installed with `pipx`.

The best mental model is:

```text
OpenAPI Generator: generate code for developers to import.
openapi-cli-gen: generate commands for humans and scripts to run.
```

## Example

With raw `curl`, nested JSON bodies get noisy:

```bash
curl -X POST "$API_URL/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John","address":{"city":"NYC","state":"NY"}}'
```

With a generated CLI:

```bash
mycli users create \
  --name John \
  --address.city NYC \
  --address.state NY
```

That command is easier to paste into runbooks, CI scripts, support docs, and
team chat.

## Why Nested Flags Matter

Many API CLIs are easy until the request body has nested objects, arrays, enums,
or dictionaries. `openapi-cli-gen` reads the OpenAPI schema and turns model
fields into command flags where possible:

```bash
--address.city NYC
--address.state NY
--retry.backoff.strategy exponential
--tags admin --tags reviewer
```

For complex payloads, JSON fallback still works:

```bash
mycli search query-points \
  --root '{"vector":[0.1,0.2,0.3,0.4],"limit":5}'
```

## Common Workflows

Internal admin CLI:

```bash
openapi-cli-gen generate \
  --spec http://localhost:8000/openapi.json \
  --name internal-admin
```

Public API wrapper:

```bash
openapi-cli-gen generate \
  --spec https://api.example.com/openapi.json \
  --name example-rest-cli
```

Runtime mode without creating files:

```bash
openapi-cli-gen run \
  --spec https://catfact.ninja/docs \
  --base-url https://catfact.ninja \
  facts get-random
```

## Tradeoffs

Generated CLIs inherit names from the OpenAPI spec. If a spec uses long
operation IDs, the generated command names can be long too.

For public wrapper packages, the best experience may be:

1. generate the complete API surface;
2. keep the full generated commands available;
3. add small wrapper-level aliases for the common workflows.

That keeps generation cheap while making the top commands feel hand-designed.

## Related Pages

- [Generate a CLI from an OpenAPI Spec](generate-cli-from-openapi.md)
- [Project README](../../README.md)
- [PyPI package](https://pypi.org/project/openapi-cli-gen/)
