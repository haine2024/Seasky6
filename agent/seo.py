"""Step 4 — SEO optimization.

Article take-aways:
  - Single-page tools are picked up fast: meta description, OG tags, schema.
  - Page speed matters: avoid heavy libs.
  - Tool must sit above the fold; SEO copy stays below.

This module runs passive checks (size budget, content depth, semantic
markup, JSON-LD presence) and reports a checklist per tool page.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class SeoCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class SeoReport:
    file: str
    score: int
    max_score: int
    checks: list[SeoCheck] = field(default_factory=list)

    def status(self) -> str:
        ratio = self.score / max(self.max_score, 1)
        if ratio >= 0.9: return "excellent"
        if ratio >= 0.7: return "good"
        if ratio >= 0.5: return "needs-work"
        return "fail"


SPEED_BUDGET_KB = 60  # single-file HTML/JS should stay tiny


def run_checks(html_path: Path) -> SeoReport:
    html = html_path.read_text(encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024

    checks = [
        SeoCheck("title tag present", '<title>' in html, ""),
        SeoCheck("meta description present", 'name="description"' in html, ""),
        SeoCheck("og tags present", 'property="og:title"' in html and 'property="og:description"' in html, ""),
        SeoCheck("canonical link present", 'rel="canonical"' in html, ""),
        SeoCheck("JSON-LD schema present", 'application/ld+json' in html, ""),
        SeoCheck("viewport meta present", 'name="viewport"' in html, ""),
        SeoCheck("dark mode CSS present", "prefers-color-scheme" in html, ""),
        SeoCheck("no external JS libs (single-file)", "<script src=" not in html, "purity favors index speed"),
        SeoCheck("file size under 60 KB", size_kb < SPEED_BUDGET_KB, f"{size_kb:.1f} KB"),
        SeoCheck("has h1", re.search(r"<h1[^>]*>.+?</h1>", html, re.S) is not None),
        SeoCheck("FAQ / extra copy section", "<h2>" in html),
        SeoCheck("site footer with policy links", 'href="/privacy.html"' in html and 'href="/about.html"' in html),
    ]
    score = sum(1 for c in checks if c.passed)
    return SeoReport(file=html_path.name, score=score, max_score=len(checks), checks=checks)


def render(report: SeoReport) -> str:
    lines = [f"# SEO report — {report.file}", ""]
    lines.append(f"Score: {report.score}/{report.max_score}  ·  Status: **{report.status().upper()}**")
    lines.append("")
    lines.append("| Check | Pass | Detail |")
    lines.append("|-------|------|--------|")
    for c in report.checks:
        lines.append(f"| {c.name} | {'✅' if c.passed else '❌'} | {c.detail} |")
    return "\n".join(lines)
