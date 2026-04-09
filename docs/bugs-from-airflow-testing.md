# Bugs Found Testing Against Live Airflow API

Tested against Airflow 3.2.0 running in Breeze (localhost:28080), 111 endpoints, 139 schemas.

## Summary

| Category | Passed | Failed | Total |
|---|---|---|---|
| GET (list/get) | 17 | 1 | 18 |
| POST (create) | 3 | 1 | 4 |
| PATCH (update) | 0 | 1 | 1 |
| DELETE | 0 | 3 | 3 |
| --help | 6 | 0 | 6 |
| **Total** | **26** | **6** | **32** |

## Bugs

### BUG-1: datetime not JSON serializable (CRITICAL)

**Trigger:** `airflow DagRun trigger-dag-run --dag-id example_bash_operator --logical-date 2026-04-09T00:00:00+00:00`

**Error:** `TypeError: Object of type datetime is not JSON serializable`

**Root cause:** pydantic-settings parses `--logical-date` into a Python `datetime` object (via `AwareDatetime` type from datamodel-code-generator). Our `_attach_cli_cmd` does `self.model_dump(exclude_none=True)` which keeps it as a `datetime`, then `httpx` tries to `json.dumps()` it and fails.

**Fix:** Use `self.model_dump(exclude_none=True, mode='json')` which serializes datetime to ISO string. Or use `model_dump_json()` then `json.loads()`.

**Severity:** Critical — blocks all endpoints with datetime fields.

---

### BUG-2: PATCH sends fields only in path OR body, not both (MEDIUM)

**Trigger:** `airflow Connection patch --connection-id my_test_postgres --conn-type postgres --host db.example.com`

**Error:** `422 Unprocessable Entity — connection_id missing from body`

**Root cause:** Our `_attach_cli_cmd` separates fields into `path_params`, `query_params`, and `body` based on the field name. If `connection_id` is both a path param AND a body field, it only goes to `path_params` and gets stripped from the body.

**Fix:** Don't strip path param fields from body when the endpoint also has a request body. Only strip them from query params.

**Severity:** Medium — breaks PATCH/PUT endpoints where the identifier is also in the body.

---

### BUG-3: DELETE returns empty body, tool treats as error (LOW)

**Trigger:** `airflow Variable delete --variable-key test_var` (after it was already deleted)

**Error:** `404 Not Found — variable not found`

**Note:** This is actually correct behavior — the resource was already deleted in a previous test. But our tool also crashes on `204 No Content` responses (successful DELETE) because it tries to parse an empty response as JSON.

**Fix:** Handle 204 responses gracefully — print "Deleted successfully" or similar instead of trying to parse JSON.

**Severity:** Low — DELETE works, but success message is wrong.

---

### BUG-4: DagSource get-dag-source requires file-token from another API call (NOT A BUG)

**Trigger:** `airflow DagSource get-dag-source --file-token test`

**Error:** `exit 2 — missing required arg` or invalid token

**Note:** This is expected — `file_token` comes from the DAG details response. Not a bug in our tool.

---

### BUG-5: Task Instance list requires both dag_id and dag_run_id (NOT A BUG)

**Trigger:** `airflow Task Instance get-task-instances --dag-id example_bash_operator --dag-run-id manual__2026-04-09T00:00:00+00:00`

**Error:** `404 — DAG Run not found`

**Note:** The dag_run_id doesn't exist because the trigger failed (BUG-1). Not a bug in our tool.

---

### BUG-6: Nested model serialization — Pydantic models not converted to dicts (LOW)

**Context:** When a body field is a nested Pydantic model (from datamodel-code-generator), `model_dump()` returns nested Pydantic objects for some fields. Our `_serialize_body()` helper handles this, but there may be edge cases with deeply nested models or enums.

**Fix:** Ensure `model_dump(mode='json')` is used consistently, which handles all serialization.

**Severity:** Low — mostly handled, but may surface with complex schemas.

---

## Commands That Work Perfectly

### GET operations
- `Version get` — version info
- `Monitor get-health` — health status
- `Pool get-pools` — list pools
- `Pool get-pool --pool-name <name>` — get specific pool
- `DAG get-dags --limit N` — list DAGs with pagination
- `DAG get-dag --dag-id <id>` — get specific DAG
- `DAG get-details --dag-id <id>` — get DAG details
- `DAG get-tags` — list DAG tags
- `Provider get` — list providers
- `Plugin get` — list plugins
- `Job get` — list jobs
- `Event Log get-event-logs --limit N` — list event logs
- `Import Error get-import-errors` — list import errors
- `DagWarning list-dag-warnings` — list warnings
- `Variable get-variables` — list variables
- `Variable get-variable --variable-key <key>` — get specific variable
- `Connection get-connections` — list connections
- `Connection get-connection --connection-id <id>` — get specific connection
- `DagRun get-dag-runs --dag-id <id> --limit N` — list DAG runs

### POST operations (create)
- `Variable post --key <key> --value <val>` — create variable
- `Pool post --name <name> --slots N` — create pool
- `Connection post --connection-id <id> --conn-type <type> --host <host>` — create connection

### --help (all work)
- Every command group shows available commands
- Every command shows correct flags with types, defaults, required markers
- Nested fields show with dot-notation
- Enum fields show choices
- Boolean fields show `--flag/--no-flag` syntax

## Priority Fixes

1. **BUG-1 (datetime serialization)** — one-line fix, unblocks trigger/backfill/scheduling
2. **BUG-2 (path+body overlap)** — small fix, unblocks PATCH/PUT with identifiers
3. **BUG-3 (DELETE 204)** — small fix, better UX for delete operations
