# Generate a CLI from an OpenAPI Spec

This guide shows how to generate a Python command line app from an OpenAPI or
Swagger spec with `openapi-cli-gen`.

Use this when you want a human-facing API CLI:

- an internal admin CLI for a FastAPI service;
- a scriptable wrapper for a public REST API;
- typed commands for support, ops, QA, or demos;
- a package users can install with `pipx install`.

If you want SDKs in many languages or generated server stubs, use OpenAPI
Generator. If you want terminal commands for humans and scripts,
`openapi-cli-gen` is built for that narrower job.

## Install

```bash
pipx install openapi-cli-gen
```

Or:

```bash
uv tool install openapi-cli-gen
```

## Preview Commands Before Generating

Use `inspect` to see the command groups and operations that would be generated:

```bash
openapi-cli-gen inspect --spec https://petstore3.swagger.io/api/v3/openapi.json
```

For a local FastAPI app:

```bash
openapi-cli-gen inspect --spec http://localhost:8000/openapi.json
```

## Run an API as a CLI Without Codegen

`run` is useful for testing a spec before creating a package:

```bash
openapi-cli-gen run \
  --spec https://catfact.ninja/docs \
  --base-url https://catfact.ninja \
  facts get-random
```

Table output works well for list endpoints:

```bash
openapi-cli-gen run \
  --spec https://catfact.ninja/docs \
  --base-url https://catfact.ninja \
  breeds get --limit 5 --output-format table
```

## Generate a Python CLI Package

Generate the package:

```bash
openapi-cli-gen generate \
  --spec https://api.example.com/openapi.json \
  --name mycli
```

Install it locally:

```bash
cd mycli
pip install -e .
```

Run it:

```bash
mycli --help
mycli users list
mycli users create --name John --email john@example.com
```

## FastAPI Example

FastAPI publishes an OpenAPI spec at `/openapi.json` by default.

While your app is running:

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

This is useful for internal admin APIs, QA workflows, smoke tests, and support
tools where a full SDK would be too heavy.

## Nested Request Bodies Become Flags

The main reason to use `openapi-cli-gen` instead of hand-written `curl` scripts
is nested request-body handling.

Instead of:

```bash
curl -X POST "$API_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"name":"John","address":{"city":"NYC","state":"NY"}}'
```

You can use flags:

```bash
mycli users create \
  --name John \
  --address.city NYC \
  --address.state NY
```

For deeply nested or unusual payloads, JSON fallback is still available:

```bash
mycli users create \
  --address '{"city":"NYC","state":"NY"}'
```

## Auth

Auth is generated from the spec's `securitySchemes`.

For a bearer token:

```bash
export MYCLI_TOKEN=sk-...
mycli users list
```

Most auth values can also be passed as flags, which override environment
variables:

```bash
mycli users list --token sk-...
```

## Output Formats

Use JSON for scripts:

```bash
mycli users list --output-format json
```

Use tables for interactive browsing:

```bash
mycli users list --output-format table
```

## When to Publish a Generated CLI

A generated wrapper is useful when:

- the upstream API already has a public OpenAPI spec;
- users currently copy `curl` commands or write small one-off scripts;
- there are repeated admin, import/export, debug, or QA workflows;
- the command names are readable enough, or you add wrapper-level aliases.

Good wrapper candidates include developer tools, self-hosted apps, search
engines, vector databases, media servers, and APIs with strong import/export
workflows.

## Related Pages

- [Project README](../../README.md)
- [Supported APIs](../supported-apis.md)
- [PyPI package](https://pypi.org/project/openapi-cli-gen/)
