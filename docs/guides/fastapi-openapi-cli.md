# Generate a CLI from a FastAPI App

FastAPI gives every app an OpenAPI spec at `/openapi.json` by default.
`openapi-cli-gen` can turn that spec into a Python command line app.

This is useful when you want:

- an internal admin CLI;
- support or QA commands;
- smoke-test commands for CI;
- a scriptable wrapper around an internal API;
- a quick way to explore endpoints without writing `curl`.

## Install

```bash
pipx install openapi-cli-gen
```

Or:

```bash
uv tool install openapi-cli-gen
```

## Start Your FastAPI App

For example:

```bash
uvicorn app.main:app --reload
```

FastAPI should expose the spec here:

```text
http://localhost:8000/openapi.json
```

You can check it with:

```bash
curl http://localhost:8000/openapi.json
```

## Preview The CLI

Before generating files, inspect the commands:

```bash
openapi-cli-gen inspect \
  --spec http://localhost:8000/openapi.json
```

This shows the API title, endpoint count, command groups, and auth schemes that
the generated CLI will use.

## Generate The CLI

```bash
openapi-cli-gen generate \
  --spec http://localhost:8000/openapi.json \
  --name internal-admin
```

Install it locally:

```bash
cd internal-admin
pip install -e .
```

Run it:

```bash
internal-admin --help
```

## Example Commands

If your FastAPI app has routes like:

```text
GET /users
POST /users
GET /users/{user_id}
```

The generated CLI will expose matching command groups and options based on the
OpenAPI operation IDs, tags, path parameters, query parameters, and request
schemas.

For example:

```bash
internal-admin users list
internal-admin users get --user-id 123
internal-admin users create --name Jane --email jane@example.com
```

Exact command names depend on your FastAPI route tags and operation IDs.

## Nested Pydantic Models Become Flags

FastAPI apps often use Pydantic models for request bodies:

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

Instead of asking users to paste JSON:

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com","address":{"city":"NYC","state":"NY"}}'
```

the generated CLI can expose nested fields as dot flags:

```bash
internal-admin users create \
  --name Jane \
  --email jane@example.com \
  --address.city NYC \
  --address.state NY
```

For complicated payloads, JSON fallback is still available:

```bash
internal-admin users create \
  --address '{"city":"NYC","state":"NY"}'
```

## Auth

If your FastAPI OpenAPI spec declares auth with `securitySchemes`,
`openapi-cli-gen` exposes matching environment variables and flags.

For a bearer token style API:

```bash
export INTERNAL_ADMIN_TOKEN=your-token
internal-admin users list
```

Or pass the token directly:

```bash
internal-admin users list --token your-token
```

## Runtime Mode For One-Off Checks

You can also call an endpoint without generating a package:

```bash
openapi-cli-gen run \
  --spec http://localhost:8000/openapi.json \
  users list
```

This is handy for quick smoke tests or debugging while the API is still moving.

## Tips For Better Generated Commands

FastAPI route metadata affects CLI quality.

Use tags to create clean command groups:

```python
@app.get("/users", tags=["users"])
def list_users():
    ...
```

Use explicit operation IDs when the default generated name is too long:

```python
@app.post("/users", tags=["users"], operation_id="create_user")
def create_user():
    ...
```

Use clear Pydantic field names. Those become CLI flags.

## When This Is A Good Fit

Use a generated FastAPI CLI when:

- the API is already described accurately by OpenAPI;
- teammates are copying `curl` snippets into runbooks;
- support or ops needs safe repeatable commands;
- QA needs quick setup/cleanup commands;
- you want a small internal tool without maintaining a hand-written wrapper.

If you need SDKs for application code, use an SDK generator. If you need commands
for humans and scripts, generate a CLI.

## Related Pages

- [Generate a CLI from an OpenAPI Spec](generate-cli-from-openapi.md)
- [OpenAPI Generator vs openapi-cli-gen](openapi-generator-vs-openapi-cli-gen.md)
- [Project README](../../README.md)
