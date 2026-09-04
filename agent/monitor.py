"""Step 7 — Monitor (lightweight, file-based).

Article take-aways:
  - 工具站前 1-3 个月是沙盒期，流量爬得慢。
  - 看 RPM 而不是只看 PV，词的价值决定一切。
  - 哪个工具稳了、哪个要换题，反馈给选题环节。

This module simulates a daily metrics ingestion so the dashboard can
show realistic-looking data without needing real GSC wiring.  In
production you'd swap `record_hit` for a real GSC + GA4 → CSV pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import csv
import datetime as dt
import json


@dataclass
class MetricRecord:
    date: str
    slug: str
    impressions: int
    clicks: int
    revenue_usd: float


METRICS_FILE = "metrics.csv"


def ensure_csv(path: Path) -> None:
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "slug", "impressions", "clicks", "revenue_usd"])


def append_metric(path: Path, rec: MetricRecord) -> None:
    ensure_csv(path)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([rec.date, rec.slug, rec.impressions, rec.clicks, round(rec.revenue_usd, 4)])


def load_metrics(path: Path) -> list[MetricRecord]:
    if not path.exists():
        return []
    out = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.append(MetricRecord(
                date=row["date"],
                slug=row["slug"],
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                revenue_usd=float(row["revenue_usd"]),
            ))
    return out


def simulate_for_slugs(slugs: list[str], base_rpm: float, days: int = 7) -> list[MetricRecord]:
    """Deterministic demo simulator: each tool has a different curve."""
    today = dt.date.today()
    out = []
    seeds = {slug: hash(slug) % 17 for slug in slugs}
    for d in range(days, 0, -1):
        day = today - dt.timedelta(days=d)
        for slug, seed in seeds.items():
            # impressions grow with day offset (recency-ish) + seed
            impressions = 80 + (days - d) * 30 + seed * 5
            clicks = max(1, impressions // 12)
            revenue = impressions * (base_rpm / 1000.0)
            out.append(MetricRecord(day.isoformat(), slug, impressions, clicks, revenue))
    return out


def aggregate(records: list[MetricRecord]) -> dict:
    by_slug: dict[str, dict] = {}
    for r in records:
        if r.slug not in by_slug:
            by_slug[r.slug] = {"impressions": 0, "clicks": 0, "revenue_usd": 0.0}
        by_slug[r.slug]["impressions"] += r.impressions
        by_slug[r.slug]["clicks"] += r.clicks
        by_slug[r.slug]["revenue_usd"] += r.revenue_usd
    total_imp = sum(v["impressions"] for v in by_slug.values())
    total_clk = sum(v["clicks"] for v in by_slug.values())
    total_rev = sum(v["revenue_usd"] for v in by_slug.values())
    ctr = (total_clk / total_imp * 100) if total_imp else 0
    rpm = (total_rev / total_imp * 1000) if total_imp else 0
    return {
        "by_slug": by_slug,
        "total_impressions": total_imp,
        "total_clicks": total_clk,
        "total_revenue_usd": round(total_rev, 4),
        "ctr_pct": round(ctr, 2),
        "rpm_usd": round(rpm, 2),
    }
