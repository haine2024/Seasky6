"""Auto Money Agent — main entry.

Runs the 7-step pipeline end-to-end:

  1. niche          — score and pick top niches from config
  2. keywords       — harvest and rank keyword ideas
  3. code_gen       — render 3 sample HTML tools (calculator / text / generator)
  4. seo            — passive SEO checks on each tool page
  5. compliance     — write about / privacy / contact + AdSense checklist
  6. deploy         — write sitemap / robots.txt / deploy manifest
  7. monitor        — simulate a week of metrics and dump a JSON summary

Usage:
  python main.py            # full demo run, writes everything to ./tools_output

Each step prints a one-line status. All artifacts are also written to
./reports/ as Markdown for human review.
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent import niche, keywords, code_gen, seo, compliance, deploy, monitor


CONFIG = HERE / "config.yaml"
TOOLS_DIR = HERE / "tools_output"
REPORTS_DIR = HERE / "reports"


def step_header(name: str) -> None:
    print(f"\n=== {name} ===")


def main() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    summary: dict = {}

    # ---- Step 1: niches
    step_header("Stage 1 — Niche ranking")
    niches = niche.load_niches(CONFIG)
    ranked = niche.rank(niches)
    print(niche.render_report(ranked))
    (REPORTS_DIR / "01_niches.md").write_text(niche.render_report(ranked), encoding="utf-8")
    summary["top_niches"] = [n.id for n in ranked[:3]]

    # ---- Step 2: keywords
    step_header("Stage 2 — Keyword research")
    ideas = keywords.harvest(CONFIG)
    print(keywords.render_report(ideas))
    (REPORTS_DIR / "02_keywords.md").write_text(keywords.render_report(ideas), encoding="utf-8")
    summary["keywords_total"] = len(ideas)
    summary["top_keywords"] = [
        {"keyword": k.keyword, "niche_id": k.niche_id, "score": k.score}
        for k in ideas[:6]
    ]

    # ---- Step 3: code generation
    step_header("Stage 3 — Code generation (3 demo tools)")
    specs = [
        code_gen.spec_for_mortgage_calc(),
        code_gen.spec_for_text_case(),
        code_gen.spec_for_password_gen(),
    ]
    written = []
    for spec in specs:
        p = code_gen.write_tool(spec, TOOLS_DIR, base_url="https://tool-station.example.com")
        size = p.stat().st_size
        print(f"  ✓ {spec.name} → {p.name} ({size:,} bytes)")
        written.append(p)
    summary["tools_written"] = [{"slug": p.stem, "bytes": p.stat().st_size} for p in written]

    # ---- Step 4: SEO
    step_header("Stage 4 — SEO optimization")
    seo_reports = []
    for p in written:
        rep = seo.run_checks(p)
        print(seo.render(rep))
        seo_reports.append(rep)
    (REPORTS_DIR / "03_seo.md").write_text(
        "\n\n".join(seo.render(r) for r in seo_reports),
        encoding="utf-8",
    )
    summary["seo_avg_score"] = round(
        sum(r.score for r in seo_reports) / len(seo_reports), 2
    ) if seo_reports else 0

    # ---- Step 5: compliance
    step_header("Stage 5 — AdSense compliance")
    policy_paths = compliance.write_policy_pages(TOOLS_DIR, [p.stem for p in written])
    print(f"  ✓ wrote {sorted(p.name for p in policy_paths.values())}")
    rep = compliance.run_checks(CONFIG, TOOLS_DIR, [p.stem for p in written])
    print(compliance.render(rep))
    (REPORTS_DIR / "04_compliance.md").write_text(compliance.render(rep), encoding="utf-8")
    summary["adsense_ready"] = rep.ready_for_adsense

    # ---- Step 6: deploy artifacts
    step_header("Stage 6 — Deploy artifacts")
    slugs = [p.stem for p in written]
    base_url = "https://tool-station.example.com"
    deploy.validate_or_raise(TOOLS_DIR, slugs, ["about.html", "privacy.html", "contact.html"])
    robots = deploy.write_robots(TOOLS_DIR, base_url)
    smap = deploy.write_sitemap(TOOLS_DIR, base_url, slugs)
    manifest = deploy.write_deploy_manifest(
        TOOLS_DIR,
        {
            "site": "tool-station",
            "owner": "owner@example.com",
            "stack": "static",
            "pages": [{"path": f"{s}.html"} for s in slugs] + [
                {"path": "index.html"}, {"path": "about.html"},
                {"path": "privacy.html"}, {"path": "contact.html"},
                {"path": "robots.txt"}, {"path": "sitemap.xml"},
            ],
            "ready_for": ["github-pages", "cloudflare-pages", "netlify", "vercel"],
            "next_step": "git init → commit → push → enable Pages on gh-pages branch",
        },
    )
    print(f"  ✓ wrote {robots.name}, {smap.name}, {manifest.name}")
    summary["deploy_files"] = [robots.name, smap.name, manifest.name]

    # ---- Step 7: monitor simulation
    step_header("Stage 7 — Monitor (simulated)")
    metrics_path = REPORTS_DIR / monitor.METRICS_FILE
    recs = monitor.simulate_for_slugs(slugs, base_rpm=7.5, days=7)
    for r in recs:
        monitor.append_metric(metrics_path, r)
    agg = monitor.aggregate(recs)
    print(json.dumps(agg, indent=2))
    summary["monitor_summary"] = agg

    # ---- Final summary dump
    (REPORTS_DIR / "00_run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    step_header("DONE — artifacts")
    print(f"  Tools deployed to:    {TOOLS_DIR}")
    print(f"  Reports + metrics:   {REPORTS_DIR}")
    print(f"  Ready for AdSense:   {summary['adsense_ready']}")
    print(f"  Avg SEO score:       {summary['seo_avg_score']}/{len(seo_reports[0].checks) if seo_reports else 0}")
    print(f"  Simulated weekly revenue (USD): {summary['monitor_summary']['total_revenue_usd']:.2f}")
    return summary


if __name__ == "__main__":
    main()
