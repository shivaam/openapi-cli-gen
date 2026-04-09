# Experiments — Completed

All 14 experiments validated. Zero blockers found.

**Test spec:** `server/spec.yaml` — 15 endpoints, 16 schemas, 6 tags
**Test server:** `server/app.py` — `uvicorn experiments.server.app:app --reload`
**Python:** `.venv/bin/python` (uv-managed, Python 3.13)

## Results Summary

| # | File | Question | Result |
|---|---|---|---|
| 1 | `01_pydantic_settings_tree.py` | Multi-command tree | 1-level only. 3-level broken. |
| 1b | `01b_manual_dispatch.py` | Manual dispatch + CliApp | **Works.** 1.1ms/run. |
| 1c | `01c_typer_tree.py` | Typer manual wiring | Works. Beautiful --help. |
| 1d | `01d_typer_from_pydantic.py` | Dynamic Typer from Pydantic | **Works.** 0.7ms. Phase 2 add-on. |
| 2 | `02_nested_flattening.py` | Depth 1/2/3 flattening | **Perfect.** All depths work. |
| 3 | `03_arrays.py` | Arrays, dicts, enums | **Perfect.** 3 list syntaxes. |
| 6 | `06_spec_parsing.py` | jsonref + openapi-pydantic | **Perfect.** 4ms total. |
| 7 | `07_model_generation.py` | datamodel-code-generator | **Works.** BaseSettings output. |
| 8 | `08_end_to_end.py` | Full pipeline | **Works.** Naming needs refinement. |
| 9 | `09_unions.py` | Discriminated unions | **Works.** Flat flags approach. |
| 10 | `10_nullable.py` | Nullable fields | **Perfect.** All patterns. |
| 11 | `11_env_vars.py` | Env var integration | **AuthConfig(BaseSettings) wins.** |
| 12 | `12_output_formatting.py` | JSON/table/YAML output | **Beautiful.** ~40 lines. |
| 13 | `13_dynamic_nested_models.py` | create_model() + CliApp | **Perfect.** All depths. |
| 14 | `14_large_spec_performance.py` | 50-500 endpoint performance | **Fast.** 500ep = 135ms startup. |

---

## Experiment 1: pydantic-settings Multi-Command Tree

**File:** `prototypes/01_pydantic_settings_tree.py`

**Finding:** pydantic-settings `CliSubCommand` only supports 1 level of nesting. Attempting 3 levels (root → group → command) fails with `KeyError` in `run_subcommand`. Named fields with `CliSubCommand[X] | None = None` fails with `CliSubCommand is not outermost annotation`.

**Flat approach works** (all commands at root level) but produces ugly names like `UsersListCmd` instead of `users list`.

**Impact:** Need manual dispatch layer for proper `mycli users list` UX.

---

## Experiment 1b: Manual Dispatch

**File:** `prototypes/01b_manual_dispatch.py`

**Finding:** ~30-line dispatch function handles group + command routing. `CliApp.run()` handles flag parsing per command. All nested flattening works.

- `mycli users list --limit 10` — works
- `mycli users create --name John --address.city NYC` — works (nested)
- `mycli --help` / `mycli users --help` / `mycli users create --help` — all work
- **Performance:** 1.1ms flat, 1.8ms nested

**Impact:** This is our v0.1 approach.

---

## Experiment 1c: Typer Manual Wiring

**File:** `prototypes/01c_typer_tree.py`

**Finding:** Typer produces beautiful colored `--help` with boxed layouts. Tab completion works. But each command requires ~15 lines of manual parameter definitions + body reconstruction.

**Impact:** Not viable for auto-generation (too much per-command code). But validates Typer UX is worth pursuing in Phase 2.

---

## Experiment 1d: Dynamic Typer from Pydantic

**File:** `prototypes/01d_typer_from_pydantic.py`

**Finding:** Walking `model.model_fields` recursively to generate `typer.Option()` dynamically works perfectly. ~80 lines of bridge code. All Typer UX (colors, completion, rich help) with zero per-command code.

- **Performance:** 0.7ms/run (fastest approach)
- Nested `--address.city` dot-notation works
- Composable via `app.add_typer()`

**Impact:** Validated as Phase 2 add-on (`--framework typer`).

---

## Experiment 2: Nested Model Flattening

**File:** `prototypes/02_nested_flattening.py`

**Finding:** pydantic-settings handles all nesting depths perfectly:

| Depth | Example | Works? |
|---|---|---|
| 1 | `--address.city NYC` | Yes |
| 2 | `--ceo.name Bob` | Yes |
| 3 | `--retry.backoff.strategy exponential` | Yes |
| JSON | `--retry '{"max_attempts": 5}'` | Yes |
| Mix | `--address '{"city":"NYC"}' --address.city SF` → SF | Yes |
| Dict | `--environment '{"K":"V"}'` | Yes |

`--help` groups nested fields under `{field} options:` headers.

**Impact:** No depth limit in our design. pydantic-settings handles it all.

---

## Experiment 3: Arrays, Dicts, Enums

**File:** `prototypes/03_arrays.py`

**Finding:** All work perfectly.

| Type | Syntax | Works? |
|---|---|---|
| `list[str]` repeated | `--tags a --tags b` | Yes |
| `list[str]` JSON | `--tags '["a","b"]'` | Yes |
| `list[str]` comma | `--tags a,b` | Yes |
| `list[int]` | `--scores 10 --scores 20` | Yes |
| `list[Object]` JSON | `--items '[{...}]'` | Yes |
| `list[Object]` repeated JSON | `--items '{...}' --items '{...}'` | Yes |
| `dict` JSON | `--env '{"K":"V"}'` | Yes |
| `dict` key=value | `--env K=V` | Yes |
| `enum` | `--role {admin,user,viewer}` | Yes, validated |
| Mixed | All together | Yes |

**Impact:** No custom array/dict/enum handling needed. pydantic-settings handles it all.

---

## Experiment 6: Spec Parsing

**File:** `prototypes/06_spec_parsing.py`

**Finding:**
- `jsonref.replace_refs()`: 0.6ms, all $ref resolved including nested
- `openapi_pydantic.parse_obj()`: 3.4ms, typed access to everything
- Circular refs: handled via lazy `JsonRef` proxies
- Security schemes: detected correctly (bearerAuth, apiKeyAuth)
- Endpoint extraction: tag grouping, params, bodies all accessible

**Impact:** Spec parsing pipeline validated. 4ms total is negligible.

---

## Experiment 7: datamodel-code-generator

**File:** `prototypes/07_model_generation.py`

**Finding:**
- Basic generation: 3.5s (one-time), 146 lines, all models correct
- `base_class="pydantic_settings.BaseSettings"`: works
- Custom class name generator: works (`APIUserCreate`, etc.)
- Discriminated union: `RootModel[NotificationEmail | NotificationSMS]`
- Enums: auto-generated (`Role`, `Strategy`, `Status`)

**Impact:** Model generation validated. 3.5s is acceptable since it's one-time during `generate`.

---

## Experiment 8: End-to-End Prototype

**File:** `prototypes/08_end_to_end.py`

**Finding:** Full pipeline works: spec → parse → extract endpoints → create_model() → dispatch → CliApp.run() → httpx call. Build time: 24ms.

**Bug found:** operationId → command name heuristic was naive (prefix-stripping produced wrong names). Easy to fix with proper operationId parsing.

**Impact:** Pipeline validated end-to-end. Command naming logic needs proper implementation.

---

## Experiment 9: Discriminated Unions

**File:** `prototypes/09_unions.py`

**Finding:** Two approaches tested:
- **JSON-only**: `--notification '{"type":"email","to":"..."}'` — works but not discoverable
- **Flat flags**: `--type email --to user@x.com --subject Hi` — works, shows all fields in --help

**Impact:** Flat flags approach chosen. All union variants' fields are exposed; `--type` discriminator selects which variant is constructed.

---

## Experiment 10: Nullable Fields

**File:** `prototypes/10_nullable.py`

**Finding:**
- `str | None = None`: optional, default None, omitting works
- `str | None` (no default): correctly shows `(required)` in --help
- Nested nullable model: omit all nested fields → entire model is `null`
- `(ifdef: required)` hint for nested required fields

**Impact:** No special handling needed. Pydantic + pydantic-settings handle all nullable patterns.

---

## Experiment 11: Environment Variables

**File:** `prototypes/11_env_vars.py`

**Finding:** Four approaches tested:
- `BaseModel` + `CliApp.run()`: does NOT read env vars (expected)
- `BaseSettings` + `CliApp.run()`: reads env vars (but pollutes all fields)
- Manual `os.environ.get()` fallback: works but fragile
- **`AuthConfig(BaseSettings)` with `env_prefix`**: cleanest approach

**Winner:** Separate `AuthConfig(BaseSettings, env_prefix="MYCLI_")` model. Created once, reads `MYCLI_TOKEN` from env. Injected into httpx client.

**Impact:** Auth design validated. Separate model, not per-command.

---

## Experiment 12: Output Formatting

**File:** `prototypes/12_output_formatting.py`

**Finding:** ~40 lines covers all formats:
- JSON: `json.dumps(indent=2)` — clean
- YAML: `yaml.dump()` — clean
- Table: `rich.table.Table` — auto-detects list vs single object vs wrapped list

Table formatter intelligently handles:
- `[{...}, {...}]` → column table
- `{"items": [...], "total": N}` → table + metadata line above
- `{key: value}` → vertical key/value table

**Impact:** Output formatter is trivial to implement. Rich tables look great.

---

## Experiment 13: Dynamic Nested Models + CliApp

**File:** `prototypes/13_dynamic_nested_models.py`

**Finding:** `pydantic.create_model()` with nested BaseModel fields works perfectly with `CliApp.run()`:
- Static nested: works
- Dynamic model + static nested type: works
- Fully dynamic (nested model also from create_model): works
- 3-level dynamic nesting: works
- Dynamic with list + dict: works

All produce correct `--help` with dot-notation groups.

**Impact:** We can build the entire command model tree dynamically from parsed schemas. No code generation needed for the command models themselves.

---

## Experiment 14: Large Spec Performance

**File:** `prototypes/14_large_spec_performance.py`

**Finding:**

| Endpoints | Build Registry | Per-Command |
|---|---|---|
| 14 | 5ms | 0.9ms |
| 50 | 12ms | 1.0ms |
| 100 | 29ms | 0.7ms |
| 200 | 58ms | 0.8ms |
| 500 | 135ms | 1.0ms |

Build is linear with endpoint count. Per-command is constant ~1ms.

**Impact:** No performance concern. Even the largest APIs (Stripe: 414 endpoints) would build in ~120ms.

---

## Decision Matrix

| | pydantic-settings (v0.1) | Typer dynamic (Phase 2) |
|---|---|---|
| Multi-command tree | Manual dispatch (~30 lines) | Native `add_typer()` |
| Nested flattening | Built-in (free) | Our bridge code (~80 lines) |
| Array handling | 3 syntaxes (free) | Need custom handling |
| Dict handling | JSON + key=value (free) | Need custom handling |
| Enum choices | Validated choices (free) | Need custom handling |
| --help quality | Plain argparse | Rich colors, boxed |
| Tab completion | No | Yes |
| Startup (500ep) | 135ms | ~140ms (similar) |
| Per-command | 1.0ms | 0.7ms |
| Code to maintain | ~30 lines dispatch | ~80 lines bridge + edge cases |
| Composability | argparse subparsers | Typer/Click groups |
