# Experiments

Prototyping different approaches before building the real thing.

**Test spec:** `server/spec.yaml` — covers all complexity levels
**Test server:** `server/app.py` — `uvicorn experiments.server.app:app --reload`

## Test Spec Coverage

| Schema | Complexity | Tests |
|---|---|---|
| Tag | Flat (2 fields) | Simple CRUD |
| UserCreate | 1-level nesting (address), array of strings, enum | Most common pattern |
| Company | 2-level nesting (ceo.name, address.city) | Our dot-notation limit |
| JobConfig | 3-level nesting (retry.backoff.strategy) | JSON fallback territory |
| OrderCreate | Array of objects (items: OrderItem[]) | Hardest flag problem |
| Notification | Discriminated union (email vs sms) | Rare but should handle |
| NullableExample | Nullable fields (3.1 style) | Must handle correctly |

---

## Experiment 1: pydantic-settings Multi-Command Tree

**Question:** Can pydantic-settings handle `mycli users list` / `mycli users create` / `mycli orders get` — nested subcommands with 15+ commands across 5 groups?

**File:** `prototypes/01_pydantic_settings_tree.py`

**Things to test:**
- [ ] Multiple command groups (users, orders, companies, jobs, tags)
- [ ] Multiple commands per group (list, create, get, update, delete)
- [ ] --help at each level (root, group, command)
- [ ] Required vs optional args
- [ ] Startup time with many commands
- [ ] Error messages for missing required args

**Finding:** _TODO_

---

## Experiment 2: Nested Model Flattening

**Question:** How does pydantic-settings handle nested models at depth 1, 2, 3? Where does UX break down?

**File:** `prototypes/02_nested_flattening.py`

**Things to test:**
- [ ] Depth 1: `--address.city NYC` (UserCreate.address.city)
- [ ] Depth 2: `--ceo.name "John"` (Company.ceo.name)
- [ ] Depth 3: `--retry.backoff.strategy exponential` (JobConfig.retry.backoff.strategy)
- [ ] --help readability at each depth
- [ ] cli_avoid_json=True behavior
- [ ] Mixing JSON and dot-notation: `--address '{"city":"NYC"}' --address.zip 10001`
- [ ] What happens at depth 4+?

**Finding:** _TODO_

---

## Experiment 3: Array Handling

**Question:** How do arrays of primitives and arrays of objects work in pydantic-settings CLI?

**File:** `prototypes/03_arrays.py`

**Things to test:**
- [ ] Array of strings: `--tags admin --tags reviewer`
- [ ] Array of strings comma: `--tags admin,reviewer`
- [ ] Array of objects: `--items '[{"product_id":"x","quantity":1}]'`
- [ ] Array of objects repeated: `--items '{"product_id":"x","quantity":1}' --items '{"product_id":"y","quantity":2}'`
- [ ] --help for array fields
- [ ] Empty arrays

**Finding:** _TODO_

---

## Experiment 4: Typer Multi-Command (for comparison)

**Question:** What does the same CLI look like in Typer? How much better is the UX?

**File:** `prototypes/04_typer_comparison.py`

**Things to test:**
- [ ] Same command structure as experiment 1
- [ ] --help formatting (colors, tables)
- [ ] Tab completion
- [ ] How nested models are handled (manual flattening)
- [ ] Code complexity comparison (lines of code)

**Finding:** _TODO_

---

## Experiment 5: Click Multi-Command (for comparison)

**Question:** What does it look like in raw Click? Is this a viable alternative?

**File:** `prototypes/05_click_comparison.py`

**Things to test:**
- [ ] Same command structure
- [ ] pydanclick integration for Pydantic models
- [ ] --help formatting
- [ ] Code complexity

**Finding:** _TODO_

---

## Experiment 6: Spec Parsing Pipeline

**Question:** Does jsonref + openapi-pydantic actually work end-to-end on our test spec?

**File:** `prototypes/06_spec_parsing.py`

**Things to test:**
- [ ] Load spec.yaml
- [ ] jsonref resolves all $ref
- [ ] openapi-pydantic parses into typed models
- [ ] Can we iterate paths and extract: tag, operationId, method, params, request body schema?
- [ ] Circular ref handling (add a self-referencing schema to test)
- [ ] Performance: time to parse

**Finding:** _TODO_

---

## Experiment 7: datamodel-code-generator Programmatic Usage

**Question:** Can we call datamodel-code-generator programmatically and get Pydantic models from our spec?

**File:** `prototypes/07_model_generation.py`

**Things to test:**
- [ ] generate() with our spec.yaml as input
- [ ] Output quality: are the models correct?
- [ ] base_class=BaseSettings — does it work?
- [ ] use_annotated=True + field_constraints=True
- [ ] Custom class name generator
- [ ] Time to generate

**Finding:** _TODO_

---

## Experiment 8: End-to-End Prototype

**Question:** Can we wire spec parsing + model generation + pydantic-settings CLI into a working prototype?

**File:** `prototypes/08_end_to_end.py`

**Things to test:**
- [ ] Parse spec → extract endpoints → build CLI → run command
- [ ] Actually make an HTTP call to the test server
- [ ] Output formatting (JSON, table)
- [ ] Auth header injection
- [ ] Total startup time

**Finding:** _TODO_

---

## Experiment 9: Discriminated Unions

**Question:** How should discriminated unions (oneOf + discriminator) work in the CLI?

**File:** `prototypes/09_unions.py`

**Things to test:**
- [ ] pydantic-settings CliSubCommand approach
- [ ] JSON-only approach (simpler)
- [ ] --help when there are union variants
- [ ] Error messages when wrong variant given

**Finding:** _TODO_

---

## Experiment 10: Nullable Fields

**Question:** How do nullable fields appear in the CLI? Can you pass null?

**File:** `prototypes/10_nullable.py`

**Things to test:**
- [ ] Optional[str] field behavior
- [ ] type: ["string", "null"] (3.1 style)
- [ ] How to pass null on CLI (--field null? omit flag?)
- [ ] Default None vs required nullable

**Finding:** _TODO_

---

## Decision Matrix (fill in after experiments)

| | pydantic-settings | Typer | Click + pydanclick |
|---|---|---|---|
| Multi-command tree | ? | ? | ? |
| Nested flattening | ? | ? | ? |
| Array handling | ? | ? | ? |
| --help quality | ? | ? | ? |
| Tab completion | ? | ? | ? |
| Startup time | ? | ? | ? |
| Lines of code | ? | ? | ? |
| Composability | ? | ? | ? |
