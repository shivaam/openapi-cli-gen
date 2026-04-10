# openai-rest-cli

**A full-coverage CLI for the OpenAI REST API.** Every endpoint — chat, completions, embeddings, images, moderations, files, vector stores, assistants, batch — exposed as a typed command. Generated from [OpenAI's official OpenAPI spec](https://github.com/openai/openai-openapi).

Built using [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen).

## Why

The official `openai` Python SDK **dropped its CLI in v1.0.0** (Nov 2023). Existing community CLIs are mostly chat-REPL tools (shell-gpt, llm, aichat) that focus on "ask GPT a question" and intentionally skip admin/scripting endpoints like Batch, Vector Stores, Files, and Fine-tuning.

This one is different: **every endpoint in the OpenAPI spec is a command**, with typed flags auto-generated from the spec. When OpenAI updates the spec, a regeneration gets you the new endpoints.

Think `kubectl` for OpenAI, not another chat REPL.

## Install

```bash
pipx install openai-rest-cli

# Or with uv
uv tool install openai-rest-cli
```

## Setup

```bash
export OPENAI_REST_CLI_TOKEN=sk-...  # your OpenAI API key
```

## Quick Start

```bash
# List all models
openai-rest-cli Models list

# Get a specific model
openai-rest-cli Models retrieve --model gpt-4o-mini

# Chat completion (GPT-4o-mini)
openai-rest-cli Chat create-completion \
  --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Hello"}]'

# Generate an embedding
openai-rest-cli Embeddings create \
  --input "Hello world" \
  --model text-embedding-3-small \
  --dimensions 8

# Classify content (moderation)
openai-rest-cli Moderations create --input "I love puppies"

# Generate an image (DALL-E)
openai-rest-cli Images create \
  --prompt "A cat coding on a laptop" \
  --model dall-e-2 \
  --size 256x256

# List files
openai-rest-cli Files list

# Vector stores
openai-rest-cli "Vector stores" list-vector-stores
openai-rest-cli "Vector stores" create-vector-store --name my_store

# Batch operations
openai-rest-cli Batch list-batches --limit 10

# Legacy text completion (GPT-3.5-turbo-instruct)
openai-rest-cli Completions create \
  --model gpt-3.5-turbo-instruct \
  --prompt "Python is" \
  --max-tokens 30
```

## What's Covered

| Group | Example commands |
|---|---|
| **Chat** | `create-completion`, `list-completions`, `get-completion` |
| **Completions** (legacy) | `create` |
| **Embeddings** | `create` |
| **Images** | `create` (DALL-E), `create-edit`, `create-variation` |
| **Audio** | `create-speech`, `create-transcription`, `create-translation` |
| **Moderations** | `create` |
| **Models** | `list`, `retrieve`, `delete` |
| **Files** | `create`, `list`, `retrieve`, `delete`, `download` |
| **Vector stores** | Full CRUD + file attach/detach |
| **Assistants** | Full lifecycle (requires `OpenAI-Beta` header) |
| **Batch** | `create`, `retrieve`, `cancel`, `list-batches` |
| **Fine-tuning** | Jobs, events, checkpoints |
| **Uploads** | Multi-part file uploads |
| **Responses** | Create, delete, get |

## Output Formats

```bash
openai-rest-cli Models list --output-format json    # default
openai-rest-cli Models list --output-format table   # rich table
openai-rest-cli Models list --output-format yaml
openai-rest-cli Models list --output-format raw
```

## Discovery

```bash
# Top-level groups
openai-rest-cli --help

# Commands in a group
openai-rest-cli Chat --help

# Flags for a specific command
openai-rest-cli Images create --help
# Shows: --prompt, --model, --size {256x256,512x512,...}, --quality {standard,hd}, etc.
```

## Real Example Session

```bash
$ openai-rest-cli Embeddings create --input "Hello" --model text-embedding-3-small --dimensions 4
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [-0.087, -0.041, 0.115, -0.205],
      "index": 0
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 1,
    "total_tokens": 1
  }
}

$ openai-rest-cli Chat create-completion \
  --model gpt-4o-mini \
  --messages '[{"role":"user","content":"Reply in 3 words"}]'
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Sure, what's up?"
      }
    }
  ],
  "usage": { "prompt_tokens": 13, "completion_tokens": 5 }
}

$ openai-rest-cli Images create --prompt "A cat coding" --model dall-e-2 --size 256x256
{
  "created": 1775806667,
  "data": [
    { "url": "https://oaidalleapiprodscus.blob.core.windows.net/..." }
  ]
}
```

## How It Works

This package is a thin wrapper:
- Embeds the OpenAI OpenAPI spec (`spec.yaml`)
- Delegates CLI generation to [openapi-cli-gen](https://github.com/shivaam/openapi-cli-gen) at runtime
- Base URL defaults to `https://api.openai.com/v1`

Since it's spec-driven, adding new endpoints is just a regeneration. No manual wrapping to fall behind.

## Limitations

- **Complex `oneOf`/`anyOf` bodies**: Some endpoints with deeply nested unions (e.g., Assistants message content with mixed types) require passing JSON via a fallback field instead of individual flags.
- **Assistants API**: Requires `OpenAI-Beta: assistants=v2` header. Not yet supported natively — you can work around by using the SDK for Assistants.
- **Streaming**: Not supported. For streaming chat, use the SDK directly.

## Not Affiliated

This is an **unofficial community CLI** built on top of OpenAI's public OpenAPI spec. It is not endorsed by or affiliated with OpenAI. The `openai` package on PyPI is the official SDK.

## License

MIT

