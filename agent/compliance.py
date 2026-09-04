"""Step 5 — AdSense compliance checker.

Article take-aways:
  - Submit AdSense after 3-5 tools + about + privacy + contact, not after traffic.
  - Privacy policy is non-negotiable.
  - Avoid adult / gambling / drugs.

This module generates static about / privacy / contact pages (so the
site is AdSense-ready out of the box) and runs a checklist.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class ComplianceReport:
    ready_for_adsense: bool
    checks: list[tuple[str, bool, str]] = field(default_factory=list)


POLICY_PAGES = {
    "about.html": """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>About — Tool Station</title>
<meta name="description" content="About this tool station: a small, fast collection of free online utilities." />
<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:0 auto;padding:32px 16px;color:#1a1a1a;background:#f7f7f5;line-height:1.6;}h1{font-weight:500;}</style>
</head><body>
<h1>About this tool station</h1>
<p>This is a small, fast, free collection of single-page utilities that solve
one specific task each. There is no login, no upload, no account. Everything
runs in your browser, and we do not store what you type.</p>
<p>The site is operated by a single person who wants to make the web a little
less annoying, one tool at a time.</p>
<p>Contact: contact@example.com</p>
<p style="margin-top:32px;font-size:.85rem;"><a href="/">Home</a></p>
</body></html>
""",
    "privacy.html": """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Privacy policy — Tool Station</title>
<meta name="description" content="Privacy policy for this tool station: we don't collect or sell your data." />
<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:0 auto;padding:32px 16px;color:#1a1a1a;background:#f7f7f5;line-height:1.6;}h1,h2{font-weight:500;}</style>
</head><body>
<h1>Privacy policy</h1>
<p><strong>Last updated:</strong> 2026-01-01</p>

<h2>Data we do not collect</h2>
<p>The tools on this site run entirely in your browser. We do not upload,
log, or store the text, numbers, or files you enter. Your inputs never leave
your device unless explicitly stated on the page.</p>

<h2>Cookies and advertising</h2>
<p>We use Google AdSense to display ads. Google may use cookies to serve ads
based on your prior visits to this site or other sites. You can opt out of
personalized advertising by visiting
<a href="https://www.google.com/settings/ads">Google Ads Settings</a>.</p>

<h2>Analytics</h2>
<p>We may use privacy-respecting aggregate analytics (no personal identifiers,
no IP storage beyond what the provider requires) to count page views.</p>

<h2>Contact</h2>
<p>For any privacy question, contact contact@example.com.</p>

<p style="margin-top:32px;font-size:.85rem;"><a href="/">Home</a></p>
</body></html>
""",
    "contact.html": """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Contact — Tool Station</title>
<meta name="description" content="Contact the operator of this tool station." />
<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:0 auto;padding:32px 16px;color:#1a1a1a;background:#f7f7f5;line-height:1.6;}h1{font-weight:500;}</style>
</head><body>
<h1>Contact</h1>
<p>The fastest way to reach us is by email:</p>
<p><strong>contact@example.com</strong></p>
<p>For bug reports about a specific tool, please include the tool name and
the browser version. We do not collect anything from this page.</p>

<p style="margin-top:32px;font-size:.85rem;"><a href="/">Home</a></p>
</body></html>
""",
    "index.html": """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Tool Station — Free online utilities</title>
<meta name="description" content="A small, fast collection of free online utilities. No signup, no upload, runs in your browser." />
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:0 auto;padding:32px 16px;color:#1a1a1a;background:#f7f7f5;line-height:1.6;}
h1,h2{font-weight:500;}
.tool-card{display:block;padding:16px 20px;margin:12px 0;background:#fff;border:1px solid #e6e4dd;border-radius:12px;text-decoration:none;color:#1a1a1a;}
.tool-card:hover{border-color:#185fa5;}
footer.site{margin-top:48px;font-size:.85rem;color:#666;display:flex;gap:12px;justify-content:space-between;flex-wrap:wrap;}
footer.site a{color:#185fa5;text-decoration:none;}
</style>
</head><body>
<h1>Tool Station</h1>
<p>Single-page utilities. No login, no upload, results in 3 seconds.</p>
<h2>Tools</h2>
__TOOL_LIST__

<footer class="site">
  <div>© 2026 Tool Station</div>
  <div>
    <a href="/about.html">About</a> ·
    <a href="/privacy.html">Privacy</a> ·
    <a href="/contact.html">Contact</a>
  </div>
</footer>
</body></html>
""",
}


def write_policy_pages(out_dir: Path, tool_files: list[str]) -> dict[str, Path]:
    """Write about / privacy / contact / index.html.
    `tool_files` is a list of relative slugs used to build index.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, content in POLICY_PAGES.items():
        if name == "index.html":
            cards = "\n".join(
                f'<a class="tool-card" href="{t}.html">{t.replace("-", " ").title()}</a>'
                for t in tool_files
            )
            content = content.replace("__TOOL_LIST__", cards)
        p = out_dir / name
        p.write_text(content, encoding="utf-8")
        paths[name] = p
    return paths


def run_checks(config_path: Path, out_dir: Path, tool_files: list[str]) -> ComplianceReport:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    ad = cfg["adsense"]
    rep = ComplianceReport(ready_for_adsense=True, checks=[])

    n_tools = len(tool_files)
    rep.checks.append((
        f"≥{ad['min_pages_required']} tool pages",
        n_tools >= ad["min_pages_required"],
        f"have {n_tools}"
    ))

    if ad.get("require_privacy_policy"):
        ok = (out_dir / "privacy.html").exists()
        rep.checks.append(("privacy.html exists", ok, ""))

    if ad.get("require_about_page"):
        ok = (out_dir / "about.html").exists()
        rep.checks.append(("about.html exists", ok, ""))

    if ad.get("require_contact_page"):
        ok = (out_dir / "contact.html").exists()
        rep.checks.append(("contact.html exists", ok, ""))

    bad_kw = ad.get("block_high_risk_keywords", [])
    rep.checks.append((
        "no high-risk keywords",
        all(not any(b in t.lower() for b in bad_kw) for t in tool_files),
        ""
    ))

    rep.ready_for_adsense = all(passed for _, passed, _ in rep.checks)
    return rep


def render(rep: ComplianceReport) -> str:
    lines = ["# AdSense compliance report", ""]
    lines.append(f"Ready for AdSense review: **{rep.ready_for_adsense}**")
    lines.append("")
    lines.append("| Check | Pass |")
    lines.append("|-------|------|")
    for name, ok, detail in rep.checks:
        lines.append(f"| {name} | {'✅' if ok else '❌'} ({detail}) |")
    return "\n".join(lines)
