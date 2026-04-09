# Stainless CLI Design Patterns (Gold Standard Reference)

Stainless builds CLIs for OpenAI, Anthropic, Cloudflare. Their design is the best reference.

## Command Structure
```
tool [resource [sub-resource]] method --flags
```

Example: `openai chat completions create --model gpt-4 --messages ...`

- Tags/resources → command groups
- operationId → method name
- Path params → required flags
- Query params → optional flags
- Request body fields → flattened flags (with depth limits)

## Nested Object Strategy (THE Key Design)

### Tier 1: Simple flags (flat fields)
```bash
my-tool users create --name "John" --age 30
```

### Tier 2: Dot notation (1 level of nesting)
```bash
my-tool users create --name.first "John" --name.last "Doe"
```

### Tier 3: JSON/YAML fallback (anything deeper)
```bash
my-tool users create --address '{"street": "123 Main", "city": "NYC"}'
# OR pipe from file:
cat user.json | my-tool users create
# OR YAML heredoc:
my-tool users create <<YAML
address:
  street: 123 Main St
  city: NYC
YAML
```

### Why 2-level max?
"If you want tab completion and proper --help documentation, your flags need to be defined statically, which rules out infinitely nested paths like --messages.0.content.0.text"

## Array Handling
- Primitives: repeated flags (`--tag admin --tag reviewer`)
- Objects: JSON/YAML input (no flag-per-element syntax)

## Stdin + Flag Merging
Pipe a base payload, override with flags. Flags win.
```bash
cat base-user.json | my-tool users create --role admin
```
Enables templating workflows.

## Output Features
- `--format json|jsonl|yaml|pretty|raw|explore`
- `--transform` with GJSON queries (like jq but built-in)
- `--format=explore` opens interactive TUI with vim keybindings
- Auto-pagination with lazy streaming to terminal pager

## File Uploads
```bash
my-tool upload --photo @abe.jpg        # @ prefix = file reference
my-tool upload --file @data://file.txt  # force base64 encoding
```

## Key Takeaways for Our Tool
1. 2-level dot notation is the sweet spot
2. Arrays of objects = JSON fallback, don't invent syntax
3. Discriminated unions = JSON fallback (they're rare)
4. Stdin merging with flag precedence is powerful
5. Resource hierarchy, not URL-based commands
6. Kebab-case everything on CLI
7. CLI wraps SDK, not raw HTTP — get retries/auth/serialization free
