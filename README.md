# You Might Be a Vibe Coder

AI gotchas for programmers, designers and industry experts, in the "You might be a… if" format, an homage to Jeff Foxworthy. Every line is original.

A static site with no dependencies beyond Python 3.9+. Gotchas are queued with future dates and released automatically by a daily rebuild.

## Layout

```
content/gotchas.json   all gotchas, past and future
site.json              title, domain, timezone, cadence, audiences
build.py               generates dist/ (only gotchas dated today or earlier)
assets/                style.css, app.js, favicon.svg
.github/workflows/     daily build + deploy to GitHub Pages
```

## Add a gotcha

Append an entry to `content/gotchas.json`:

```json
{
  "id": "short-url-slug",
  "date": "2026-12-04",
  "audience": "programmers",
  "line": "the rest of the sentence after \"You might be a vibe coder if\".",
  "gotcha": "The serious takeaway, one or two sentences."
}
```

- `audience` is `programmers`, `designers` or `leaders` (shown as "Industry experts").
- `id` becomes the permalink: `/g/short-url-slug/`. Don't change it once published.
- Entries are numbered in date order, so keep new dates after the last published one.

## Preview locally

```bash
python build.py                     # as of today
python build.py --today 2026-11-20  # as the site will look on a future date
python -m http.server -d dist 8000  # open http://localhost:8000
```

## Publish on GitHub Pages

1. Push this folder to a GitHub repo (branch `main`).
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. Settings → Pages → **Custom domain**: `vibecoder.itmusings.com` (matches `cname` in `site.json`), then tick **Enforce HTTPS** once the certificate is issued.
4. At your DNS provider for itmusings.com, add a `CNAME` record: `vibecoder` → `<your-github-username>.github.io`.

The workflow runs on every push and daily at 00:05 IST, so a gotcha dated tomorrow appears tomorrow without you doing anything.

### Things to know

- **Public repo = public queue.** Future gotchas are hidden from the site but visible in a public repository. Use a private repo (GitHub Pages from private repos needs a paid plan) if spoilers matter.
- **GitHub pauses scheduled workflows after 60 days without commits.** Adding gotchas keeps it alive; if it pauses, re-enable it from the Actions tab.
- **Different domain or path?** Edit `base_url` and `cname` in `site.json`. Internal links are relative, so the site also works under a subpath such as `itmusings.com/vibecoder/` (set `cname` to `""` in that case).
- Other static hosts (Netlify, Cloudflare Pages) work too: build command `python build.py`, output directory `dist`.
