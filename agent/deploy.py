"""Step 6 — Deploy helper.

Article take-aways:
  - Static single-file pages → free / ultra-cheap hosting.
  - GitHub Pages, Cloudflare Pages, Netlify, Vercel all qualify.
  - Submit sitemap after deploy.

This module:
  - Validates all expected files exist on disk.
  - Writes a sitemap.xml.
  - Writes a robots.txt.
  - Writes a deploy.json manifest (so a real CI step / `gh-pages`
    push can pick it up).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import datetime as dt


SITEMAP_TPL = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""

ROBOTS_TXT_TPL = """User-agent: *
Allow: /

Sitemap: {origin}/sitemap.xml
"""


def write_robots(out_dir: Path, origin: str) -> Path:
    p = out_dir / "robots.txt"
    p.write_text(ROBOTS_TXT_TPL.format(origin=origin.rstrip("/")), encoding="utf-8")
    return p


def write_sitemap(out_dir: Path, origin: str, slugs: list[str]) -> Path:
    today = dt.date.today().isoformat()
    urls = []
    for s in slugs + ["", "about", "privacy", "contact"]:
        loc = f"{origin.rstrip('/')}/{s}.html" if s else f"{origin.rstrip('/')}/"
        urls.append(
            f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>"
        )
    content = SITEMAP_TPL.format(urls="\n".join(urls))
    p = out_dir / "sitemap.xml"
    p.write_text(content, encoding="utf-8")
    return p


def write_deploy_manifest(out_dir: Path, payload: dict) -> Path:
    p = out_dir / "deploy.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def validate_or_raise(out_dir: Path, slugs: list[str], policy_pages: list[str]) -> None:
    for s in slugs:
        f = out_dir / f"{s}.html"
        if not f.exists():
            raise FileNotFoundError(f"missing tool file: {f}")
    for p in policy_pages:
        f = out_dir / p
        if not f.exists():
            raise FileNotFoundError(f"missing policy file: {f}")
