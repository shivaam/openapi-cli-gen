# openapi-cli-gen

Generate typed Python CLIs from OpenAPI specs with Pydantic model flattening into CLI flags.

**The problem:** You have a FastAPI (or any) REST API with an OpenAPI spec. You want a CLI client. Today you either hand-write one or use `curl`. No tool takes nested request body schemas and flattens them into ergonomic `--flag` arguments.

**The solution:** `openapi-cli-gen` reads your OpenAPI spec, generates Pydantic models, and produces a Typer CLI where nested request bodies become flat, typed CLI flags with dot-notation.

```bash
# Instead of this:
curl -X POST /api/dags/my_dag/runs -d '{"conf": {"key": "val"}, "logical_date": "2024-01-01T00:00:00Z"}'

# You get this:
mycli dags trigger my_dag --conf '{"key": "val"}' --logical-date 2024-01-01T00:00:00Z
```

## Status

Early development. Not yet functional.

## License

MIT
