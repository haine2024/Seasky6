#!/usr/bin/env python3
# ============================================================
# inject_adsense.py — One-shot helper to inject AdSense code
# into all generated HTML files in tools_output/.
#
# Usage:
#   python inject_adsense.py
#
# After running:
#   1. git add tools_output/ && git commit -m "adsense: inject verification code"
#   2. git push (so GitHub Pages redeploys)
#   3. In AdSense UI, make sure the submitted URL is
#      https://YOUR_NAME.github.io/YOUR_REPO/  (with full path)
#   4. Click "Verify" again — AdSense crawls that page, sees
#      your publisher ID, and accepts.
# ============================================================

from pathlib import Path
import re
import sys

# 1. ---- Publisher ID comes from the user ----
# Set this once. Re-run the script to update.
PUBLISHER_ID = "ca-pub-1956340995769142"

# 2. ---- The script tag AdSense gives you ----
# Keep on one line to avoid edge-case parser issues.
ADSENSE_SCRIPT = (
    f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
    f'?client={PUBLISHER_ID}" crossorigin="anonymous"></script>'
)

# 3. ---- A safe visible ad unit on the homepage only ----
# Format: auto, responsive. Falls back gracefully if no ad fills.
ADSENSE_INS_BANNER = f"""
<!-- AdSense auto ad (top of homepage) -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{PUBLISHER_ID}"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
  (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
"""

TOOLS_DIR = Path(__file__).parent / "tools_output"

# Match an existing AdSense script (any publisher) to avoid duplicates.
RE_ADSENSE = re.compile(
    r'<script[^>]*pagead2\.googlesyndication\.com[^>]*></script>',
    re.IGNORECASE,
)


def inject(path: Path, is_homepage: bool = False) -> bool:
    """Inject AdSense script into <head>. Returns True if changed."""
    html = path.read_text(encoding="utf-8")

    # Skip if AdSense already present (idempotent)
    if RE_ADSENSE.search(html):
        return False

    # Inject right before </head>
    if "</head>" not in html:
        print(f"  ⚠ {path.name}: no </head>, skipped")
        return False

    new_html = html.replace(
        "</head>",
        f"  {ADSENSE_SCRIPT}\n  </head>",
        1,
    )

    # For the homepage, also drop in a visible ad slot at the top of <body>.
    if is_homepage and "<body" in new_html:
        # Insert right after the first opening <body ...>
        m = re.search(r"<body[^>]*>", new_html)
        if m:
            insert_at = m.end()
            new_html = (
                new_html[:insert_at]
                + "\n"
                + ADSENSE_INS_BANNER
                + new_html[insert_at:]
            )

    path.write_text(new_html, encoding="utf-8")
    return True


def main() -> int:
    if not TOOLS_DIR.is_dir():
        print(f"tools_output/ not found at {TOOLS_DIR}")
        print("Run `python main.py` first to generate it.")
        return 1

    html_files = sorted(p for p in TOOLS_DIR.glob("*.html"))
    if not html_files:
        print("No HTML files in tools_output/")
        return 1

    changed = 0
    for p in html_files:
        is_home = p.name == "index.html"
        if inject(p, is_homepage=is_home):
            print(f"  ✓ {p.name}{' (homepage + visible ad)' if is_home else ''}")
            changed += 1
        else:
            print(f"  · {p.name} (already had AdSense)")

    print()
    print(f"Done. {changed}/{len(html_files)} file(s) updated.")
    print(f"Publisher ID: {PUBLISHER_ID}")
    print()
    print("Next steps:")
    print("  1. git add tools_output/ && git commit -m 'adsense: inject code'")
    print("  2. git push   (GitHub Actions will redeploy)")
    print("  3. In AdSense UI, confirm the URL field is the FULL site URL:")
    print("     https://haine2024.github.io/auto-money-agent/")
    print("  4. Click Verify again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
