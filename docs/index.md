# openapi-cli-gen

Generate human-facing Python CLIs from OpenAPI, Swagger, and FastAPI specs.

`openapi-cli-gen` turns API schemas into command line apps: endpoint groups
become subcommands, parameters become typed options, and nested request bodies
can become dot flags like `--address.city NYC`.

```bash
pipx install openapi-cli-gen

openapi-cli-gen generate \
  --spec https://api.example.com/openapi.json \
  --name mycli
```

Project:

- [GitHub repository](https://github.com/shivaam/openapi-cli-gen)
- [PyPI package](https://pypi.org/project/openapi-cli-gen/)
- [Publishing these docs with GitHub Pages](pages-publishing.md)

## Start Here

- [Generate a CLI from an OpenAPI Spec](guides/generate-cli-from-openapi.md)
- [Generate a CLI from a FastAPI App](guides/fastapi-openapi-cli.md)
- [OpenAPI Generator vs openapi-cli-gen](guides/openapi-generator-vs-openapi-cli-gen.md)

## Blog

- [Turn an OpenAPI Spec Into a CLI People Can Actually Use](blog/2026-05-26-openapi-spec-to-cli.md)

## Why This Exists

OpenAPI specs are usually used to generate SDKs, server stubs, and docs. Those
are useful, but they are not the only thing a spec can generate.

For support, ops, QA, demos, and internal admin workflows, a terminal command is
often the better interface:

```bash
mycli users create \
  --name Jane \
  --email jane@example.com \
  --address.city NYC \
  --address.state NY
```

That is the lane for `openapi-cli-gen`: not another SDK directory, but commands
humans and scripts can run.

## Good Fits

- FastAPI apps with `/openapi.json`
- Internal admin APIs
- Self-hosted apps with REST APIs
- Search and vector databases
- Import/export workflows
- QA setup and cleanup endpoints
- API wrappers that should be installable with `pipx`

## Feedback Wanted

The most useful feedback is a real OpenAPI spec that makes generated CLIs
awkward: unusual auth, nested bodies, arrays of objects, multipart uploads,
unions, or very large schemas.

[Open a spec compatibility report](https://github.com/shivaam/openapi-cli-gen/issues/new?template=spec-compatibility-report.yml)
or start from the [GitHub repository](https://github.com/shivaam/openapi-cli-gen).
