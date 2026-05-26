# Lightweight Marketing Tracking

Last updated: 2026-05-26.

X analytics are not reliable yet, so treat X as a distribution channel and use
observable downstream signals to judge whether the launch is working.

## Manual Snapshot Cadence

Capture this once per day for the first week after launch, then twice per week.

| Date | GitHub stars | GitHub issues | PyPI downloads | X followers | Notes |
|---|---:|---:|---:|---:|---|
| 2026-05-26 | 1 | 0 |  |  | Launch thread + comparison image posted; repo description and topics updated for FastAPI/Typer/developer-tools discovery. |
| 2026-05-26 | 1 | 0 |  |  | RustMailer first-target brief created; extracted embedded ReDoc spec, verified 82 endpoints/12 groups, and generated a temporary `rustmailer-rest-cli` prototype. |
| 2026-05-26 | 1 | 0 |  |  | NeoDB second-target brief created; verified public spec at `https://neodb.social/api/openapi.json`, inspected 75 endpoints/11 groups, generated a temporary `neodb-rest-cli`, and ran a live read-only search command. |
| 2026-05-26 | 1 | 0 |  |  | Open Wearables third-target brief created; verified public spec at `https://api.openwearables.io/openapi.json`, inspected 110 endpoints/30 groups, generated a temporary `open-wearables-rest-cli`, and ran a live read-only provider-list command. |

## Action Log

Use this for posts, backlink PRs, GitHub Discussions, wrapper validation, and
paid experiments.

| Date | Channel | Action | Link | Result | Next step |
|---|---|---|---|---|---|
| 2026-05-26 | planning | Created 8-week slow-burn calendar | `docs/marketing/8-week-star-growth-calendar.md` | Pending execution | Publish README/docs/PyPI changes, then start Week 1. |
| 2026-05-26 | GitHub metadata | Added live repo topics `openapi-cli`, `openapi-to-cli`, `api-cli`, `command-line`, and `swagger-cli` | https://github.com/shivaam/openapi-cli-gen | Topics live; stars still 1 | Watch GitHub search/referrers after README/docs are pushed. |
| 2026-05-26 | docs/SEO | Added FastAPI-specific guide | `docs/guides/fastapi-openapi-cli.md` | Targets `fastapi cli generator`, `fastapi openapi cli`, and `fastapi admin cli` searches | Use this guide in the `r/FastAPI` post after docs are pushed. |
| 2026-05-26 | blog | Drafted long-form post | `docs/blog/2026-05-26-openapi-spec-to-cli.md` | Ready for GitHub Pages/dev.to/Hashnode/GitHub Discussion after docs are pushed | Publish once repo links resolve publicly. |
| 2026-05-26 | blog | Added platform publishing pack | `docs/blog/publishing-pack.md` | dev.to, Hashnode, GitHub Discussion, X, Reddit, and LinkedIn copy ready | Publish/cross-post after README/docs links are live. |
| 2026-05-26 | docs/SEO | Added simple docs homepage for GitHub Pages | `docs/index.md` | Ready if Pages is enabled from `/docs`; live repo Pages currently disabled | Enable GitHub Pages after docs are pushed, then update repo homepage if desired. |
| 2026-05-26 | GitHub Pages | Added Pages workflow and publishing runbook | `.github/workflows/pages.yml`, `docs/pages-publishing.md` | Workflow will publish `docs/` after push to `main` and Pages source is set to GitHub Actions | Push docs, enable Pages, then use Pages URL in blog/community links. |
| 2026-05-26 | GitHub Pages | Enabled live GitHub Pages with `build_type=workflow` via `gh api` | https://shivaam.github.io/openapi-cli-gen/ | Pages enabled; site waits for workflow/docs to be pushed to `main`; stars still 1 | Push `.github/workflows/pages.yml` and `docs/`, then run Pages workflow. |
| 2026-05-26 | GitHub Pages | Switched Pages to branch mode and added static HTML entrypoints | https://shivaam.github.io/openapi-cli-gen/ | Added `docs/index.html` and `docs/blog/openapi-spec-to-cli.html` so Pages can serve without a build step | Push HTML entrypoints and verify the public URL no longer 404s. |

## What To Check

- GitHub repository:
  - Stars and watchers.
  - New issues or discussions.
  - Traffic/views/clones if available in GitHub Insights.
  - Referrers in Insights after links are shared outside X.
- PyPI:
  - Project page visibility and recent downloads.
  - Package install names for generated wrappers.
- X:
  - Likes, reposts, replies, profile clicks if visible.
  - Replies from people sharing specs or naming competitors.
  - Bookmark/save count if visible.
- Search/community:
  - Mentions of `openapi-cli-gen`.
  - Comments on Reddit/Hacker News/LinkedIn if posted there.

## Link Hygiene

- Keep the canonical repo link simple in public posts:
  `https://github.com/shivaam/openapi-cli-gen`
- For channels where link tracking matters, use separate landing links or URL
  variants only when they do not look spammy.
- Add a short "where did you find this?" issue template later if inbound issues
  start appearing.

## Interpretation Rules

- No visible X tracking does not mean zero impact. Developer tools often convert
  through GitHub visits, stars, package installs, and saved posts rather than
  immediate replies.
- If a post gets no visible engagement after 24 hours, repurpose the idea for a
  community with stronger intent instead of reposting the same copy.
- The highest-value signal is not impressions; it is someone sending a real spec
  that breaks the tool.
