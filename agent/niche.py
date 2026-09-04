"""Step 1 — Niche scoring.

Article take-away:
  - Tool station > content station because 一次做对，长期复利。
  - 选 niche 看 3 个信号：
      1) 是不是"完成任务"型（输入 → 立即拿结果）
      2) 关键词 RPM 上限（金融 / 软件 > 通用 > 娱乐）
      3) 大厂是否垄断（PDF 转 Word 跳过，房贷子项进入）

This module ranks niches from config.yaml and produces a working
selection that downstream modules consume.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import yaml


@dataclass
class Niche:
    id: str
    name: str
    difficulty: str  # low / mid / high
    avg_rpm_usd: tuple  # (low, high)
    score: float = 0.0
    enabled: bool = True

    def mid_rpm(self) -> float:
        lo, hi = self.avg_rpm_usd
        return (lo + hi) / 2


def load_niches(config_path: Path) -> list[Niche]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    out = []
    for n in cfg.get("niches", []):
        if not n.get("enabled", True):
            continue
        out.append(
            Niche(
                id=n["id"],
                name=n["name"],
                difficulty=n["difficulty"],
                avg_rpm_usd=tuple(n["avg_rpm_usd"]),
                enabled=True,
            )
        )
    return out


def score_niche(niche: Niche) -> float:
    """Composite score: RPM weight × difficulty penalty."""
    rpm = niche.mid_rpm()
    diff_penalty = {"low": 1.0, "mid": 0.85, "high": 0.7}[niche.difficulty]
    return rpm * diff_penalty


def rank(niches: Iterable[Niche]) -> list[Niche]:
    ranked = sorted(niches, key=score_niche, reverse=True)
    for n in ranked:
        n.score = round(score_niche(n), 2)
    return ranked


def top(niches: list[Niche], k: int = 3) -> list[Niche]:
    return rank(niches)[:k]


def render_report(ranked: list[Niche]) -> str:
    lines = ["# Stage 1 — Niche ranking", ""]
    lines.append("| Rank | ID | Name | Difficulty | RPM mid (USD) | Score |")
    lines.append("|------|------|------|-----------|---------------|-------|")
    for i, n in enumerate(ranked, 1):
        lines.append(
            f"| {i} | {n.id} | {n.name} | {n.difficulty} | "
            f"${n.mid_rpm():.1f} | {n.score:.2f} |"
        )
    lines.append("")
    lines.append("Take-aways:")
    lines.append("- Score = RPM mid × difficulty multiplier (low=1.0, mid=0.85, high=0.7).")
    lines.append("- Top 3 → drive keyword research and code generation.")
    return "\n".join(lines)
