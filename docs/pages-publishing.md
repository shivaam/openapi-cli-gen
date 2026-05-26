# Publishing Docs With GitHub Pages

This repo publishes the `docs/` directory as a lightweight GitHub Pages site.

The goal is to create a durable, indexable surface for:

- OpenAPI-to-CLI guides;
- FastAPI CLI searches;
- comparison content;
- the long-form blog post;
- links back to the GitHub repo and PyPI.

## Files

- `docs/index.md`: site home.
- `docs/guides/`: public guides.
- `docs/blog/`: blog drafts and publishing pack.
- GitHub Pages source: branch `main`, folder `/docs`.

## First-Time Setup

After the docs are pushed to `main`:

1. Open the GitHub repo settings.
2. Go to **Pages**.
3. Set source to **Deploy from a branch**.
4. Set branch to `main` and folder to `/docs`.
5. Wait for GitHub Pages to publish the Pages URL.

Expected URL:

```text
https://shivaam.github.io/openapi-cli-gen/
```

## After Pages Is Live

Update the repo homepage if the Pages site is the best first click:

```bash
gh repo edit shivaam/openapi-cli-gen \
  --homepage https://shivaam.github.io/openapi-cli-gen/
```

Keep PyPI linked prominently from the docs homepage and README.

## Tracking

After enabling or changing Pages, add a row to `docs/marketing/tracking.md`:

```md
| YYYY-MM-DD | GitHub Pages | Enabled docs site | https://shivaam.github.io/openapi-cli-gen/ | Pending indexing | Use as canonical blog/link target. |
```

Then check weekly:

- GitHub stars;
- GitHub traffic/referrers;
- whether Google indexes the Pages URL;
- whether the blog post appears for long-tail queries.
