# Changelog

All notable changes to this project will be documented here.

## [0.1.0] - 2026-09-04

### Added
- 7-step pipeline: niche → keywords → code_gen → seo → compliance → deploy → monitor.
- 3 demo tools: mortgage equal-payment-vs-principal calculator, text case converter, strong password generator.
- Auto-generated AdSense-required pages: about / privacy / contact / index / sitemap / robots.
- 12-point passive SEO checker (all generated tools score 12/12).
- Static monitor dashboard with KPIs and per-tool revenue breakdown.
- GitHub Pages deployment via GitHub Actions (`.github/workflows/deploy.yml`).
- Push helper scripts for both Bash (`push_to_github.sh`) and Windows cmd (`push_to_github.bat`).

### Repository layout
- `main.py` — pipeline entrypoint.
- `agent/` — 7 modules (one per pipeline stage).
- `tools_output/` — generated static site (committed so the first deploy works without CI history).
- `config.yaml` — niche / keyword seeds / compliance thresholds.
- `.github/workflows/deploy.yml` — CI rebuild + Pages deploy on push to `main`.
- `.gitignore` — excludes `reports/`, `dashboard/`, runtime logs, IDE files.
- `push_to_github.{sh,bat}` — one-click helper.
