"""Step 2 — Keyword research.

Article take-away:
  - 关键词要看 3 件事：搜索意图（任务型）、RPM 价值、长尾而非红海。
  - "PDF 转 Word" 这种巨头词跳过；"等额本息 vs 等额本金 计算" 这种细分词捡漏。

This module produces a list of `KeywordIdea` from `config.yaml` seed
words. In production you'd plug in a real source (Google Suggest,
AdsKeyword API, GSC data). For the demo, we apply a deterministic
scoring rubric so the pipeline is reproducible.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml
import re


@dataclass
class KeywordIdea:
    keyword: str
    niche_id: str
    intent: str = "transactional"   # transactional / commercial / informational
    value_tier: str = "neutral"    # high / mid / neutral
    competition: str = "low"        # low / mid / high
    monthly_volume_est: int = 0
    score: float = 0.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# 词 → RPM 价值的高价值信号
HIGH_VALUE_SIGNALS = [
    "mortgage", "loan", "interest", "tax", "vat", "salary", "insurance",
    "crypto", "trading", "forex", "stocks", "finance", "budget",
    "invoice", "accounting", "audit", "compliance",
]
MID_VALUE_SIGNALS = [
    "image", "pdf", "color", "palette", "font", "json", "csv", "regex",
    "developer", "code", "html", "css", "seo",
]
LOW_VALUE_SIGNALS = [
    "weather", "joke", "quote", "meme", "game",
]


def classify_value(kw: str) -> tuple[str, str]:
    """Return (value_tier, rationale)."""
    kw_l = kw.lower()
    for s in HIGH_VALUE_SIGNALS:
        if s in kw_l:
            return "high", f"signal='{s}'"
    for s in MID_VALUE_SIGNALS:
        if s in kw_l:
            return "mid", f"signal='{s}'"
    for s in LOW_VALUE_SIGNALS:
        if s in kw_l:
            return "neutral", f"low-value signal='{s}'"
    # 多词长尾默认给中性偏 mid
    word_count = len(kw_l.split())
    if word_count >= 4:
        return "mid", "long-tail multi-word"
    return "neutral", "default neutral"


def detect_intent(kw: str) -> str:
    """Most tool stations are transactional intent."""
    action_words = [
        "calculate", "compute", "convert", "format", "generate",
        "check", "test", "validate", "encode", "decode", "remove",
        "compare", "split", "merge", "resize",
    ]
    kw_l = kw.lower()
    for w in action_words:
        if w in kw_l:
            return "transactional"
    return "commercial"


def estimate_volume_stub(kw: str) -> int:
    """Deterministic placeholder. Real impl would call keyword API."""
    # 4+ words → ~50-300, 3 words → ~300-1500, 2 words → ~1500-8000
    word_count = len(kw.split())
    if word_count >= 5:
        return 80
    if word_count == 4:
        return 220
    if word_count == 3:
        return 900
    return 2500


def classify_competition(kw: str) -> str:
    """Heuristic: longer phrases tend to be less competitive."""
    wc = len(kw.split())
    if wc >= 5:
        return "low"
    if wc == 4:
        return "low"
    if wc == 3:
        return "mid"
    return "high"


def score(keyword: str, niche_id: str) -> KeywordIdea:
    value_tier, rat = classify_value(keyword)
    intent = detect_intent(keyword)
    comp = classify_competition(keyword)
    vol = estimate_volume_stub(keyword)
    # composite score
    value_w = {"high": 3.0, "mid": 1.5, "neutral": 0.8}[value_tier]
    intent_w = {"transactional": 1.4, "commercial": 1.0, "informational": 0.6}[intent]
    comp_w = {"low": 1.4, "mid": 1.0, "high": 0.4}[comp]
    s = (vol / 100.0) * value_w * intent_w * comp_w
    return KeywordIdea(
        keyword=keyword,
        niche_id=niche_id,
        intent=intent,
        value_tier=value_tier,
        competition=comp,
        monthly_volume_est=vol,
        score=round(s, 2),
        rationale=f"{rat}; intent={intent}; comp={comp}",
    )


def harvest(config_path: Path) -> list[KeywordIdea]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    out = []
    for niche_id, kws in cfg.get("keywords_seeds", {}).items():
        for kw in kws:
            out.append(score(kw, niche_id))
    return sorted(out, key=lambda k: k.score, reverse=True)


def render_report(ideas: list[KeywordIdea]) -> str:
    lines = ["# Stage 2 — Keyword research", ""]
    lines.append("| Score | Keyword | Niche | Intent | Value | Comp | Vol/mo |")
    lines.append("|-------|---------|-------|--------|-------|------|--------|")
    for k in ideas:
        lines.append(
            f"| {k.score:.2f} | {k.keyword} | {k.niche_id} | {k.intent} | "
            f"{k.value_tier} | {k.competition} | {k.monthly_volume_est} |"
        )
    return "\n".join(lines)
