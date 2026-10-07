#!/usr/bin/env python3
"""Build the static site into dist/.

Only gotchas dated on or before "today" (in the timezone set in site.json) are
published, so you can queue weeks of content and let the daily rebuild release
each one on its date. Future gotchas never reach dist/.

    python build.py                     # build for today
    python build.py --today 2026-11-20  # preview the site as of a future date
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
LEAD = "You might be a vibe coder if"
REQUIRED = ("id", "date", "audience", "line", "gotcha")


def esc(s):
    return html.escape(str(s), quote=True)


def nice_date(d):
    return f"{d.day} {d.strftime('%b %Y')}"


def load():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    site["base_url"] = site["base_url"].rstrip("/")
    items = json.loads((ROOT / "content" / "gotchas.json").read_text(encoding="utf-8"))
    seen = set()
    for i, g in enumerate(items):
        missing = [k for k in REQUIRED if not g.get(k)]
        if missing:
            raise SystemExit(f"gotcha #{i + 1} is missing {', '.join(missing)}")
        if g["id"] in seen:
            raise SystemExit(f"duplicate id: {g['id']}")
        seen.add(g["id"])
        if g["audience"] not in site["audiences"]:
            raise SystemExit(f"{g['id']}: unknown audience '{g['audience']}'")
        g["_date"] = dt.date.fromisoformat(g["date"])
        g["_order"] = i
    # Numbers are fixed by schedule order, so #12 stays #12 forever.
    items.sort(key=lambda g: (g["_date"], g["_order"]))
    for n, g in enumerate(items, 1):
        g["_num"] = n
    return site, items


def full_text(g):
    return f"{LEAD} {g['line']}"


def share_links(g, url):
    text = quote(full_text(g))
    u = quote(url, safe="")
    return (
        f'<a class="btn" href="https://www.linkedin.com/sharing/share-offsite/?url={u}" '
        f'target="_blank" rel="noopener">LinkedIn</a>'
        f'<a class="btn" href="https://x.com/intent/post?text={text}&amp;url={u}" '
        f'target="_blank" rel="noopener">X</a>'
    )


def comments_on(site):
    c = site.get("comments") or {}
    return all(c.get(k) for k in ("repo", "repo_id", "category", "category_id"))


def comment_link(href):
    return f'<a class="btn btn-comment" href="{href}">&#128172; Comment</a>'


def comments_section(site):
    if not comments_on(site):
        return ""
    c = site["comments"]
    return f"""<section id="comments" class="comments">
  <h2>Comments</h2>
  <p class="muted comments-note">Comments live in GitHub Discussions. Sign in with GitHub to join in.</p>
  <script src="https://giscus.app/client.js"
    data-repo="{esc(c['repo'])}" data-repo-id="{esc(c['repo_id'])}"
    data-category="{esc(c['category'])}" data-category-id="{esc(c['category_id'])}"
    data-mapping="pathname" data-strict="1" data-reactions-enabled="1" data-emit-metadata="0"
    data-input-position="top" data-theme="preferred_color_scheme" data-lang="en" data-loading="lazy"
    crossorigin="anonymous" async></script>
</section>"""


def card(g, site, root, *, size="small", heading="h2", link=True):
    url = f"{site['base_url']}/g/{g['id']}/"
    aud = g["audience"]
    comment = comment_link("#comments" if not link else f"{root}g/{g['id']}/#comments") if comments_on(site) else ""
    line = esc(g["line"])
    if link:
        line = f'<a href="{root}g/{g["id"]}/">{line}</a>'
    return f"""<article class="gotcha gotcha--{size}" data-audience="{aud}">
  <div class="meta"><span class="num">#{g['_num']:03d}</span><span class="aud aud--{aud}">{esc(site['audiences'][aud])}</span><time datetime="{g['date']}">{nice_date(g['_date'])}</time></div>
  <p class="lead">You might be a vibe coder <span class="kw">if</span>&hellip;</p>
  <{heading} class="line">&hellip;{line}</{heading}>
  <p class="takeaway"><span class="label">The gotcha</span>{esc(g['gotcha'])}</p>
  <div class="actions"><button class="btn copy" type="button" data-url="{esc(url)}">Copy link</button>{share_links(g, url)}{comment}</div>
</article>"""


def page(site, *, title, description, path, root, body, year, og_type="website"):
    canonical = f"{site['base_url']}/{path}"
    return f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(site['title'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="alternate" type="application/rss+xml" title="{esc(site['title'])}" href="{root}feed.xml">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<header class="masthead"><div class="wrap">
  <a class="brand" href="{root}"><span class="brand-mark">if</span><span>{esc(site['title'])}</span></a>
  <nav><a href="{root}#archive">Archive</a><a href="{root}blog/">Blog</a><a href="{root}#about">About</a><a href="{root}#me">About me</a><a href="{root}feed.xml">RSS</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site-footer"><div class="wrap">
  <p>The &ldquo;You might be a&hellip; if&rdquo; format is Jeff Foxworthy&rsquo;s, from his classic &ldquo;You might be a redneck&rdquo; routine. This site borrows the shape as an affectionate tribute. Every line here is original, and the site is not affiliated with or endorsed by Mr. Foxworthy.</p>
  <p>&copy; {year} {esc(site['author'])} &middot; <a href="{esc(site['home_site'])}">{esc(site['home_site'].split('//')[-1])}</a></p>
</div></footer>
<script src="{root}assets/app.js" defer></script>
</body>
</html>
"""


def load_posts(site):
    """Posts are content/posts/*.md with a small front-matter block."""
    posts = []
    folder = ROOT / "content" / "posts"
    for f in sorted(folder.glob("*.md")) if folder.exists() else []:
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not m:
            raise SystemExit(f"{f.name}: missing front matter")
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        for k in ("title", "date"):
            if not meta.get(k):
                raise SystemExit(f"{f.name}: missing {k}")
        meta["slug"] = meta.get("slug") or f.stem
        meta["_date"] = dt.date.fromisoformat(meta["date"])
        meta["_body"] = m.group(2).strip()
        posts.append(meta)
    slugs = [p["slug"] for p in posts]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate post slug")
    return posts


def md_inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def markdown(src):
    """Just enough Markdown for blog posts: paragraphs, ## headings, > quotes, - lists, inline marks."""
    out = []
    for block in re.split(r"\n\s*\n", src.strip()):
        lines = block.strip().splitlines()
        first = lines[0]
        if first.startswith("#"):
            level = min(len(first) - len(first.lstrip("#")), 4)
            out.append(f"<h{level}>{md_inline(first.lstrip('#').strip())}</h{level}>")
        elif all(l.startswith(">") for l in lines):
            inner = " ".join(l[1:].strip() for l in lines)
            out.append(f"<blockquote><p>{md_inline(inner)}</p></blockquote>")
        elif all(re.match(r"[-*] ", l) for l in lines):
            out.append("<ul>" + "".join(f"<li>{md_inline(l[2:])}</li>" for l in lines) + "</ul>")
        else:
            out.append(f"<p>{md_inline(' '.join(l.strip() for l in lines))}</p>")
    return "\n".join(out)


def post_teaser(p, root):
    summary = f'<p class="post-summary">{md_inline(p["summary"])}</p>' if p.get("summary") else ""
    return f"""<article class="post-teaser">
  <time datetime="{p['date']}">{nice_date(p['_date'])}</time>
  <h3><a href="{root}blog/{p['slug']}/">{esc(p['title'])}</a></h3>
  {summary}
</article>"""


def build_blog_index(site, posts, year):
    root = "../"
    items = "\n".join(post_teaser(p, root) for p in posts) or '<p class="muted">The first post is on its way.</p>'
    body = f"""<section class="blog-head">
  <p class="eyebrow">// Longer thoughts on building software with AI</p>
  <h1>The Blog</h1>
</section>
<section class="post-list">
{items}
</section>"""
    return page(site, title=f"Blog | {site['title']}", description="Experiences with vibe coding: the good code, the gotchas and the lessons.",
                path="blog/", root=root, body=body, year=year)


def build_post(site, p, newer, older, year):
    root = "../../"
    url = f"{site['base_url']}/blog/{p['slug']}/"
    u = quote(url, safe="")
    nav = '<nav class="pager">'
    nav += f'<a href="{root}blog/{older["slug"]}/">&larr; Older</a>' if older else "<span></span>"
    nav += f'<a href="{root}blog/">All posts</a>'
    nav += f'<a href="{root}blog/{newer["slug"]}/">Newer &rarr;</a>' if newer else "<span></span>"
    nav += "</nav>"
    body = f"""<article class="post">
  <header class="post-header">
    <p class="eyebrow"><a href="{root}blog/">// Blog</a></p>
    <h1>{esc(p['title'])}</h1>
    <p class="post-meta">{esc(site['author'])} &middot; <time datetime="{p['date']}">{nice_date(p['_date'])}</time></p>
  </header>
  <div class="post-body">
{markdown(p['_body'])}
  </div>
  <div class="actions post-actions"><button class="btn copy" type="button" data-url="{esc(url)}">Copy link</button><a class="btn" href="https://www.linkedin.com/sharing/share-offsite/?url={u}" target="_blank" rel="noopener">LinkedIn</a><a class="btn" href="https://x.com/intent/post?text={quote(p['title'])}&amp;url={u}" target="_blank" rel="noopener">X</a>{comment_link("#comments") if comments_on(site) else ""}</div>
</article>
{comments_section(site)}
{nav}"""
    return page(site, title=f"{p['title']} | {site['title']}", description=p.get("summary") or p["title"],
                path=f"blog/{p['slug']}/", root=root, body=body, year=year, og_type="article")


def build_home(site, published, upcoming, year, posts=()):
    root = ""
    latest, rest = published[0], published[1:]
    nxt = ""
    if upcoming:
        d = upcoming[0]["_date"]
        nxt = f'<p class="next">Next gotcha drops <strong>{d.strftime("%A")}, {nice_date(d)}</strong>. New ones land {esc(site["cadence"])}.</p>'
    chips = '<button type="button" class="chip" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" class="chip chip--{k}" data-filter="{k}" aria-pressed="false">{esc(v)}</button>'
        for k, v in site["audiences"].items()
    )
    archive = "\n".join(card(g, site, root) for g in rest) or '<p class="muted">The archive fills up from here.</p>'
    body = f"""<section class="intro">
  <p class="eyebrow">// {esc(site['tagline'])}</p>
</section>
<section class="today" aria-label="Latest gotcha">
{card(latest, site, root, size="hero")}
{nxt}
</section>
{build_home_blog(posts)}
<section id="archive" class="archive">
  <div class="archive-head"><h2>Previously</h2><div class="filters" role="group" aria-label="Filter by audience">{chips}</div></div>
  <div class="archive-list">
{archive}
  </div>
  <p class="muted archive-empty" hidden>Nothing for this audience yet. Give it a week.</p>
</section>
<section id="about" class="about">
  <h2>What is this?</h2>
  <p>Vibe coding is building software by describing what you want and accepting what the AI hands back. It is fast, fun and occasionally ruinous. Each entry here is a one-liner you might recognize, followed by the real gotcha behind the laugh.</p>
  <p>It is written for programmers, designers and the industry experts who approve the budgets. New entries arrive {esc(site['cadence'])}. Follow along by <a href="feed.xml">RSS</a>.</p>
{build_epigraph(site)}
</section>
{build_about_me(site, year)}"""
    return page(site, title=site["title"], description=site["tagline"], path="", root=root, body=body, year=year)


def build_home_blog(posts):
    if not posts:
        return ""
    p = posts[0]
    more = '<a class="more" href="blog/">All posts &rarr;</a>' if len(posts) > 1 else ""
    return f"""<section class="home-blog" aria-label="From the blog">
  <div class="home-blog-head"><span class="label">From the blog</span>{more}</div>
{post_teaser(p, "")}
</section>"""


def build_epigraph(site):
    ep = site.get("epigraph")
    if not ep:
        return ""
    lines = "<br>\n    ".join(esc(l) for l in ep["lines"])
    intro = f'<p class="epigraph-intro">{esc(ep["intro"])}</p>' if ep.get("intro") else ""
    return f"""  <figure class="epigraph">
    {intro}
    <blockquote><p>{lines}</p></blockquote>
    <figcaption>&mdash; {ep['source']}</figcaption>
  </figure>"""


def build_about_me(site, year):
    me = site.get("about_me")
    if not me:
        return ""
    home = site["home_site"]
    home_link = f'<a href="{esc(home)}">{esc(home.split("//")[-1])}</a>'
    paras = "\n".join(f"  <p>{p.replace('{home_link}', home_link)}</p>" for p in me["paragraphs"])
    stats = [
        (str(me["in_industry_since"]), "in the industry since"),
        (f"{year - me['in_industry_since']}+", "years writing software"),
        (str(me["blogging_since"]), "blogging since"),
    ]
    stat_html = "".join(f'<div class="stat"><span class="stat-num">{esc(n)}</span><span class="stat-label">{esc(l)}</span></div>' for n, l in stats)
    links = " &middot; ".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in me.get("links", []))
    return f"""<section id="me" class="me">
  <h2>About me</h2>
  <p class="me-name">{esc(me['name'])}</p>
  <div class="stats">{stat_html}</div>
{paras}
  <p class="me-links">{links}</p>
</section>"""


def build_gotcha(site, g, newer, older, year):
    root = "../../"
    nav = '<nav class="pager">'
    nav += f'<a href="{root}g/{older["id"]}/">&larr; Older</a>' if older else "<span></span>"
    nav += f'<a href="{root}">All gotchas</a>'
    nav += f'<a href="{root}g/{newer["id"]}/">Newer &rarr;</a>' if newer else "<span></span>"
    nav += "</nav>"
    body = f"""<section class="today">
{card(g, site, root, size="hero", heading="h1", link=False)}
</section>
{comments_section(site)}
{nav}"""
    return page(
        site,
        title=f"…{g['line']} | {site['title']}",
        description=f"{full_text(g)} The gotcha: {g['gotcha']}",
        path=f"g/{g['id']}/",
        root=root,
        body=body,
        year=year,
        og_type="article",
    )


def build_feed(site, published, tz, posts=()):
    items = []
    for p in posts[:20]:
        url = f"{site['base_url']}/blog/{p['slug']}/"
        when = dt.datetime.combine(p["_date"], dt.time(0, 5), tzinfo=tz)
        items.append(f"""  <item>
    <title>{esc(p['title'])}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{format_datetime(when)}</pubDate>
    <category>Blog</category>
    <description>{esc(p.get('summary') or p['title'])}</description>
  </item>""")
    for g in published[:40]:
        url = f"{site['base_url']}/g/{g['id']}/"
        when = dt.datetime.combine(g["_date"], dt.time(0, 5), tzinfo=tz)
        items.append(f"""  <item>
    <title>{esc(full_text(g))}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{format_datetime(when)}</pubDate>
    <category>{esc(site['audiences'][g['audience']])}</category>
    <description>{esc('The gotcha: ' + g['gotcha'])}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(site['title'])}</title>
  <link>{site['base_url']}/</link>
  <atom:link href="{site['base_url']}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>{esc(site['tagline'])}</description>
  <language>en</language>
{chr(10).join(items)}
</channel>
</rss>
"""


def build_404(site, year):
    root = site["base_url"] + "/"
    body = """<section class="today"><article class="gotcha gotcha--hero">
  <p class="lead">You might be a vibe coder <span class="kw">if</span>&hellip;</p>
  <h1 class="line">&hellip;you followed a link the AI swore was real.</h1>
  <p class="takeaway"><span class="label">The gotcha</span>This page doesn&rsquo;t exist. Head back to the <a href="/">latest gotcha</a>.</p>
</article></section>"""
    return page(site, title=f"Not found | {site['title']}", description="Page not found", path="404.html", root=root, body=body, year=year)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", help="build as if today were YYYY-MM-DD (for previews)")
    ap.add_argument("--out", help="output directory (default: dist/)")
    args = ap.parse_args()
    global DIST
    if args.out:
        DIST = Path(args.out).resolve()

    site, items = load()
    tz = ZoneInfo(site["timezone"])
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz).date()

    published = sorted((g for g in items if g["_date"] <= today), key=lambda g: (g["_date"], g["_order"]), reverse=True)
    upcoming = [g for g in items if g["_date"] > today]
    if not published:
        raise SystemExit(f"nothing is published as of {today}; the earliest gotcha is dated {items[0]['date']}")

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    year = today.year

    posts = sorted((p for p in load_posts(site) if p["_date"] <= today), key=lambda p: p["_date"], reverse=True)
    write(DIST / "index.html", build_home(site, published, upcoming, year, posts))
    write(DIST / "blog" / "index.html", build_blog_index(site, posts, year))
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        write(DIST / "blog" / p["slug"] / "index.html", build_post(site, p, newer, older, year))
    for i, g in enumerate(published):
        newer = published[i - 1] if i > 0 else None
        older = published[i + 1] if i + 1 < len(published) else None
        write(DIST / "g" / g["id"] / "index.html", build_gotcha(site, g, newer, older, year))
    write(DIST / "feed.xml", build_feed(site, published, tz, posts))
    write(DIST / "404.html", build_404(site, year))

    urls = [f"{site['base_url']}/", f"{site['base_url']}/blog/"] + [f"{site['base_url']}/blog/{p['slug']}/" for p in posts] \
        + [f"{site['base_url']}/g/{g['id']}/" for g in published]
    write(DIST / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site['base_url']}/sitemap.xml\n")
    if site.get("cname"):
        write(DIST / "CNAME", site["cname"] + "\n")

    if not comments_on(site):
        print("Note: comments are off until comments.repo_id and comments.category_id are set in site.json (see README).")
    print(f"Built {len(published)} published gotchas and {len(posts)} blog post(s) as of {today}; {len(upcoming)} gotchas queued"
          + (f", next on {upcoming[0]['date']}." if upcoming else "."))


if __name__ == "__main__":
    main()
