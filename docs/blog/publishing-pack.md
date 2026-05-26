# Blog Publishing Pack

Last updated: 2026-05-26.

Source post:

```text
docs/blog/2026-05-26-openapi-spec-to-cli.md
```

Canonical repo:

```text
https://github.com/shivaam/openapi-cli-gen
```

Primary goal: get qualified developers to the GitHub repo or to share real
OpenAPI specs that should become CLIs. Do not ask for stars in the article body.

## Recommended Publishing Order

1. Push repo README/docs so GitHub links resolve.
2. Publish updated PyPI metadata if doing a release.
3. Publish the blog on one canonical surface.
4. Cross-post lightly to one or two platforms with canonical links.
5. Use the post as the link for GitHub Discussion, X, and Reddit follow-ups.

Recommended canonical surface:

- If GitHub Pages is available: GitHub Pages first.
- If no site exists yet: dev.to first, because it has built-in developer
  discovery and canonical URL support.

## dev.to Version

Front matter:

```yaml
---
title: Turn an OpenAPI Spec Into a CLI People Can Actually Use
published: false
description: OpenAPI specs are not only for SDKs and docs. They can generate human-facing Python CLIs with typed flags and nested request bodies flattened into command options.
tags: openapi, python, cli, fastapi
canonical_url: https://github.com/shivaam/openapi-cli-gen
---
```

Opening note to add under the title:

```md
I built a small open-source Python tool in this space and would love feedback
from people with real OpenAPI specs, especially FastAPI apps or internal APIs.
```

End note:

```md
If you have a public OpenAPI spec that would make an awkward generated CLI, I
would love to test it: https://github.com/shivaam/openapi-cli-gen
```

Best tags:

```text
openapi, python, cli, fastapi
```

## Hashnode Version

Title:

```text
Turn an OpenAPI Spec Into a CLI People Can Actually Use
```

Subtitle:

```text
OpenAPI specs already know your endpoints, schemas, and auth. They can also become human-facing command line apps.
```

Tags:

```text
OpenAPI, Python, CLI, FastAPI, Developer Tools
```

Canonical URL:

```text
https://github.com/shivaam/openapi-cli-gen
```

End note:

```md
I am looking for real OpenAPI specs that stress this idea: weird auth, nested
request bodies, multipart uploads, arrays of objects, unions, and large schemas.
Repo: https://github.com/shivaam/openapi-cli-gen
```

## GitHub Discussion Version

Category:

```text
Show and tell
```

Title:

```text
Turn an OpenAPI spec into a CLI people can actually use
```

Intro:

```md
I wrote this up as a longer explanation of why `openapi-cli-gen` exists:

OpenAPI specs are usually used for SDKs, server stubs, and docs. I think there
is also a smaller but useful lane: generating human-facing command line apps for
support, ops, QA, internal admin tools, and scriptable API workflows.
```

Then paste the blog body without YAML front matter.

Closing question:

```md
The most useful feedback would be examples:

- What API workflows do you still run through copied `curl`?
- Would you ship a generated CLI for an internal FastAPI app?
- What OpenAPI spec would make this break or feel awkward?
```

## X / Twitter Promo

Post 1:

```text
OpenAPI specs are usually used to generate SDKs and docs.

But they already know enough to generate a human-facing CLI too: endpoints, schemas, auth, enums, and nested request bodies.

I wrote up the idea behind openapi-cli-gen:
<blog-url>
```

Post 2:

```text
The annoying part of API CLIs is not query params. It is nested request bodies.

If your OpenAPI schema knows `address.city`, your CLI can expose:

mycli users create --address.city NYC

Longer writeup:
<blog-url>
```

## Reddit Link Post

Use only after participating or when the post is directly useful to the
community. Prefer text posts over bare links.

### r/FastAPI

Title:

```text
Using FastAPI's OpenAPI spec to generate an internal CLI
```

Text:

````md
I wrote up a longer explanation of a pattern I have been exploring: using
FastAPI's `/openapi.json` to generate an internal Python CLI for support, ops,
QA, or smoke-test workflows.

The main idea is that request bodies can become flags instead of pasted JSON:

```bash
internal-admin users create \
  --name Jane \
  --address.city NYC \
  --address.state NY
```

Writeup:
<blog-url>

Repo:
https://github.com/shivaam/openapi-cli-gen

I would especially like feedback from people with real FastAPI apps. Would this
be useful for internal/admin workflows, or would you rather keep using SDKs and
curl?
````

## LinkedIn Promo

```text
OpenAPI specs are usually treated as inputs for SDKs, server stubs, and docs.

I think there is another practical use: generating human-facing CLIs for support,
ops, QA, and internal admin workflows.

If the spec already knows your request schema, a command can expose nested fields
as flags instead of asking users to paste JSON.

I wrote up the idea here:
<blog-url>
```

## Tracking

After publishing, add a row to `docs/marketing/tracking.md`:

```md
| YYYY-MM-DD | blog | Published OpenAPI-to-CLI article | <url> | Pending | Share once on X and use as Week 1 owned-channel link. |
```

Check after 24-48 hours:

- GitHub stars;
- GitHub traffic/referrers;
- comments or replies;
- specs shared;
- PyPI project views/downloads if available.
