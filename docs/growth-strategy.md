# Growth Strategy: openapi-cli-gen

## 1. Pre-Built CLIs for Popular APIs (Instant Value)

Generate CLIs for APIs people actually use and publish them. People discover our tool through the generated CLIs.

| API | Why | Effort |
|---|---|---|
| **GitHub** (551 endpoints) | Every developer uses it. `gh` exists but is limited. | Medium — large spec |
| **Stripe** (414 endpoints) | Every startup. No official CLI. | Hard — complex spec |
| **Cloudflare** | Huge user base. Official CLI exists but limited. | Medium |
| **Vercel** | Dev-focused. No CLI for many endpoints. | Easy |
| **Supabase** | Growing fast. CLI exists but API-incomplete. | Easy |
| **PocketBase** | Trendy, self-hosted. No CLI. | Easy |
| **Hetzner Cloud** | Popular EU hosting. Has OpenAPI spec. | Easy |
| **DigitalOcean** | Has spec. `doctl` exists but this shows the comparison. | Medium |
| **FastAPI projects on GitHub** | Any FastAPI app with >100 stars → generate a CLI, PR it to them | Varies |

**The play**: publish `pip install github-cli-gen` or `pip install stripe-cli-gen` packages that are just generated wrappers. Each one's README links back to openapi-cli-gen.

## 2. Launch Posts

### Hacker News
- Title: "Show HN: Generate a CLI from any OpenAPI spec — nested models become flat --flags"
- Lead with the curl vs CLI comparison
- Show the Airflow CRUD demo (real API, not toy)
- Show the cat breeds table (visual hook)
- Link to "Try it now" commands
- Best time: Tuesday-Thursday, 9-11am ET

### Reddit
- r/Python — "I built a tool that turns any OpenAPI spec into a CLI with nested model flattening"
- r/FastAPI — "Auto-generate a CLI for your FastAPI app from its OpenAPI spec"
- r/devops — "Generate CLIs for your internal APIs without writing boilerplate"
- r/commandline — "Flat --flags instead of JSON blobs for any REST API"

### Dev.to / Hashnode blog post
- "Why every API should have a CLI (and how to generate one in 10 seconds)"
- Tutorial format: install → try catfact → generate for your own API → ship it

### Twitter/X thread
- GIF/video of the terminal showing: install → catfact → breeds table → Airflow CRUD
- Tag @tiangolo (FastAPI), @samuel_colvin (Pydantic), @charliermarsh (Ruff/uv)

## 3. Integrations & Ecosystem

### FastAPI plugin/docs mention
- PR to FastAPI docs: "Generate a CLI from your FastAPI app" tutorial
- Create `fastapi-cli-gen` wrapper that auto-discovers the running app's spec

### Pydantic ecosystem
- Blog post on pydantic's blog about "pydantic-settings as a CLI framework"
- Shows how we use pydantic-settings for nested model flattening

### awesome-openapi list
- PR to add openapi-cli-gen to https://github.com/APIs-guru/awesome-openapi3

### awesome-python list
- PR to add under "Command Line Tools" or "API Development"

### datamodel-code-generator mention
- We're a great showcase of their tool used at runtime
- PR to their README or blog mentioning us

## 4. Conference Talks / Meetups

- PyCon lightning talk: "5 lines to a CLI for any API"
- FastAPI meetup: demo generating CLI from a live FastAPI app
- Local Python meetup: tutorial/workshop

## 5. Content Ideas

### Blog posts
1. "The gap nobody filled: OpenAPI to CLI" (problem statement, competitor analysis)
2. "How pydantic-settings turns nested models into --flags" (technical deep dive)
3. "I replaced 1,900 lines of Airflow CLI code with 4 lines" (case study)
4. "Testing openapi-cli-gen against 6 real APIs" (results, edge cases found)

### Demo videos
- 60-second terminal recording: install → catfact → breeds table
- 3-minute walkthrough: generate CLI for your own API
- Airflow demo: CRUD connections, trigger DAGs

## 6. Community Building

### GitHub
- Good first issues labeled for contributors
- CONTRIBUTING.md with clear setup instructions
- Issue templates for "Spec doesn't work" (attach spec, we debug)
- Discussions enabled for Q&A

### Discord/Slack
- Not yet — too early. Wait for 100+ stars.

## 7. Priority Order

**Week 1: Launch**
1. HN Show HN post
2. r/Python + r/FastAPI posts
3. Tweet thread with GIF

**Week 2: Ecosystem**
4. PR to awesome-openapi, awesome-python
5. Dev.to tutorial blog post
6. Generate + publish 2-3 API CLIs (GitHub, Stripe, or simpler ones)

**Week 3+: Deepen**
7. FastAPI docs PR
8. More blog posts
9. Conference talk submission
10. Pre-built CLI packages for popular APIs

## 8. Metrics to Track

- GitHub stars (vanity but signals credibility)
- PyPI downloads/week
- GitHub issues opened (signal of real usage)
- Specs reported as not working (feedback loop)
