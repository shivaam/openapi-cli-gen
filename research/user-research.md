# User Research: What People Want from OpenAPI CLI Tools

## The #1 Ask: Request Body Fields as --flags

Every community, every language, every tool — users want `--name John --age 30` not `--data '{"name":"John","age":30}'`.

Sources:
- openapi-cli-generator#43: "It seems non-intuitive to know all body params for a POST/PUT/PATCH"
- restish#236: "Not all of my users are familiar with CLI shorthand, and writing JSON can be cumbersome"
- Typer#111: 66 thumbs-up + 28 hearts for Pydantic model → CLI params
- Typer#154: 64 thumbs-up for dataclass → CLI generation
- pydantic-typer#10: Users want --foo and --bar, not --params.foo and --params.bar

## Top Pain Points (Ranked by Cross-Ecosystem Frequency)

### 1. Nested Model Flattening
Every project struggles with this. No solution handles it well.
- How deep should dot-notation go?
- Stainless (gold standard): 2-level max, then JSON fallback
- pydantic-settings: unlimited depth but UX degrades
- Every bridge library (pydantic-typer, pydanclick): hitting walls

### 2. Lists of Complex Objects (Universally Unsolved)
`list[SomeModel]` on the CLI — no library handles it.
- pydantic-typer#6: relies on correct flag ordering, fragile
- pydanclick#20: author says "reaching the limit of what the library can do"
- Stainless: explicitly falls back to JSON/YAML for arrays of objects

### 3. Robustness with Real-World Specs
Tools crash on GitHub, Stripe, Figma, Bitbucket APIs.
- restish#295: stack overflow on Bitbucket spec (1GB goroutine limit)
- restish#188: OOM on 4000-line spec with circular refs
- progenitor: fails on GitHub, GitLab, Stripe, Figma APIs

### 4. Auth Should Auto-Configure from Spec
- restish#275: "I'm surprised I need to manually configure auth even though it is described via security schemas in the OpenAPI spec"
- openapi-cli-generator#12: auth is manual even when spec defines schemes

### 5. Single Source of Truth (CLI + Config + Env)
- Typer#111: "My dream solution would allow a common data model filled from CLI, config files, interactive inputs"
- pydanclick#30: "creating a single source of truth"
- pydantic-settings achieves this but has rough edges

### 6. Code Generation Quality is Poor
- HN: "The python libs are especially worthless. All functions are *kwargs"
- HN: "generated code can be very shitty for some combinations of spec and language"
- openapi-python-client: 82 open issues, sole maintainer stepping back

### 7. Schema Composition (allOf/oneOf/anyOf) Breaks Everything
- openapi-python-client: #1 source of pain across 2+ years
- allOf loses fields entirely (#1392)
- oneOf inside allOf completely ignored (#1328)
- Naming collisions when schema names map to Python identifiers

### 8. Distribution as Standalone Tool
- openapi-cli-generator#16: "Make binary self-contained"
- restish#273: "Distribute with pre-configured API"
- Users want to ship the CLI as their product's tool

### 9. Command Organization by Tags/Resources
- restish#224: operations with same name under different tags collide
- openapi-cli-generator#33: want `container rm` not `container-rm`
- Stainless: resource-based hierarchy is the right pattern

### 10. Selective Generation
- openapi-python-client#55: only generate for certain tags/endpoints
- Important for large APIs (GitHub: 744 endpoints, Stripe: 414)

## What Doesn't Exist (The Gap)

No tool in ANY language does all of:
1. Read OpenAPI spec
2. Generate typed Python CLI code (not runtime interpretation)
3. Flatten nested request bodies into --flags
4. Handle auth from spec
5. Produce distributable CLI package
6. Support config files + env vars + CLI flags with clear precedence

The closest: Stainless (commercial, Go-only, closed-source)
