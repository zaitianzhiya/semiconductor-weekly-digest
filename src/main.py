"""Orchestrator: collect → filter → score → AI → render pipeline."""

import argparse
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

from src.collectors.base import EventRecord
from src.collectors.real_search import RealSearchCollector
from src.filters.dedup import Deduplicator
from src.filters.quality import QualityFilter
from src.filters.scorer import Scorer
from src.render.markdown_weekly import MarkdownRenderer

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    """Load all YAML config files and merge into one dict."""
    config: dict = {}
    for filename in ["sources.yml", "keywords.yml", "quality.yml"]:
        path = ROOT / "config" / filename
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            config.update(data)
    return config


# ── Semiconductor domain keyword → category mapping ──
SEMI_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "#foundry": [
        "foundry", "TSMC", "台积电", "Samsung foundry", "Intel foundry",
        "2nm", "3nm", "5nm", "GAA", "FinFET", "nanometer", "wafer fab",
        "capacity expansion", "fab investment", "node", "process technology",
        "代工", "制程", "晶圆厂", "量产", "产能", "N2", "N3", "GAA",
        "CFET", "Rapidus", "SMIC", "中芯", "华虹", "Hua Hong",
    ],
    "#memory": [
        "DRAM", "NAND", "HBM", "HBM3", "HBM4", "memory chip",
        "storage", "SSD", "Flash", "DDR5", "LPDDR",
        "Samsung memory", "SK Hynix", "SK hynix", "Micron",
        "CXMT", "长鑫", "YMTC", "长江存储", "存储", "内存",
        "合约价", "现货价", "contract price",
    ],
    "#equipment": [
        "ASML", "lithography", "EUV", "DUV", "光刻机", "光刻",
        "Applied Materials", "Lam Research", "KLA", "TEL",
        "etch", "deposition", "CVD", "ALD", "inspection", "metrology",
        "刻蚀", "沉积", "检测", "硅片", "光刻胶", "特气", "靶材",
        "wafer fab equipment", "semiconductor equipment",
        "北方华创", "中微公司", "NAURA", "AMEC",
        "equipment billings", "book-to-bill",
    ],
    "#eda_ip": [
        "EDA", "Synopsys", "Cadence", "Mentor", "Siemens EDA",
        "ARM", "Arm ", "RISC-V", "RISC V", "x86", "ISA",
        "instruction set", "chip design tool", "IP core",
        "UCIe", "BoW", "chiplet interconnect",
        "EDA 工具", "处理器IP", "指令集",
    ],
    "#ai_chip": [
        "NVIDIA", "GPU", "Nvidia", "AMD Instinct", "MI300", "MI400",
        "Blackwell", "Hopper", "Rubin", "B200", "B100", "H100", "H200",
        "AI chip", "AI accelerator", "TPU", "Trainium", "Inferentia",
        "NPU", "neural processor", "Ascend", "昇腾", "寒武纪",
        "AI处理器", "AI芯片", "推理芯片", "训练芯片",
        "datacenter GPU", "edge AI", "TOPS", "FLOPS",
    ],
    "#advanced_packaging": [
        "CoWoS", "advanced packaging", "chiplet", "3D IC",
        "hybrid bonding", "glass core", "glass substrate",
        "InFO", "EMIB", "Foveros", "through silicon via", "TSV",
        "先进封装", "三维集成", "异构集成", "扇出", "硅通孔",
        "chip on wafer", "system in package", "SiP",
    ],
    "#china_semi": [
        "中国半导体", "国产替代", "自主可控", "国产化",
        "国产芯片", "国产DUV", "国产EUV", "国产光刻",
        "国产设备", "国产材料", "国产EDA",
        "SMIC", "中芯国际", "Hua Hong", "华虹半导体",
        "YMTC", "长江存储", "CXMT", "长鑫存储",
        "chip export control China", "China semiconductor breakthrough",
        "大基金", "国家集成电路", "信创", "自主化",
    ],
    "#policy_geopolitics": [
        "export control", "sanction", "BIS", "entity list",
        "CHIPS Act", "CHIPS for America", "EU Chips Act",
        "export restriction", "technology ban",
        "出口管制", "制裁", "实体清单", "技术封锁",
        "semiconductor subsidy", "chip incentive",
        "chip war", "technology sovereignty",
        "semiconductor policy", "trade restriction",
        "Japan chip subsidy", "Korea chip act", "EU semiconductor",
        "MATCH Act", "FDPR",
    ],
}


def _auto_categorize(record: EventRecord, config: dict) -> list[str]:
    """Semiconductor-domain keyword classification."""
    text = f"{record.title} {record.description}".lower()
    matched: list[str] = []
    for cat_id, keywords in SEMI_CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            matched.append(cat_id)
    return matched[:3]  # max 3 categories per event


def _merge_records(records: list[EventRecord]) -> list[EventRecord]:
    """Merge records with same event_id, combining citation chains."""
    merged: dict[str, EventRecord] = {}
    for r in records:
        if r.event_id in merged:
            existing = merged[r.event_id]
            existing_keys = {c.source_key for c in existing.citations}
            for c in r.citations:
                if c.source_key not in existing_keys:
                    existing.citations.append(c)
            # Take the longer description
            if r.description and len(r.description) > len(existing.description or ""):
                existing.description = r.description
        else:
            merged[r.event_id] = r
    return list(merged.values())


def run_weekly(config: dict):
    """Full weekly pipeline: collect from all Tier 1 + Tier 2 sources."""
    print(f"[Weekly] Starting pipeline — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    records: list[EventRecord] = []

    sources_cfg = config.get("sources", {})
    enabled_sources = {k: v for k, v in sources_cfg.items() if v.get("enabled", True)}

    print(f"[Weekly] Collecting from {len(enabled_sources)} sources...")

    for source_key, source_cfg in enabled_sources.items():
        try:
            collector = RealSearchCollector(config, source_key)
            collector.gh_token = os.environ.get("GH_TOKEN", "")
            items = collector.collect()
            for item in items:
                item.categories = _auto_categorize(item, config)
            records.extend(items)
            if items:
                print(f"  [{source_key}] {len(items)} items — {source_cfg.get('name', source_key)}")
        except Exception as e:
            print(f"  [{source_key}] FAILED: {e}")

    if not records:
        print("[Weekly] No records collected — check source configuration.")
        return

    # Merge + dedup
    merged = _merge_records(records)
    print(f"[Weekly] Merged: {len(merged)} unique events (from {len(records)} raw)")

    dedup = Deduplicator(str(ROOT / "data" / "state.json"))
    new_records, seen = dedup.deduplicate(merged)
    print(f"[Weekly] Dedup: {len(new_records)} new / {seen} already seen")

    if not new_records:
        print("[Weekly] All events already seen this cycle.")
        return

    # Filter + score
    qf = QualityFilter(config)
    scorer = Scorer(config)

    new_records = qf.filter(new_records)
    new_records = scorer.score(new_records)
    new_records.sort(key=lambda r: r.confidence_score, reverse=True)

    grade_counts = {}
    for r in new_records:
        g = r.confidence_grade
        grade_counts[g] = grade_counts.get(g, 0) + 1
    grade_str = ", ".join(f"{k}:{v}" for k, v in sorted(grade_counts.items()))
    print(f"[Weekly] Filtered+Scored: {len(new_records)} events — {grade_str}")

    # AI deep analysis
    deep_analysis = ""
    try:
        from src.ai.llm_client import LLMClient
        from src.ai.deep_analyzer import DeepAnalyzer

        client = LLMClient()
        analyzer = DeepAnalyzer(client, ROOT / "prompts")
        top_n = min(len(new_records), 15)
        deep_analysis = analyzer.analyze(new_records, top_n=top_n)
        print(f"[Weekly] AI deep analysis generated ({len(deep_analysis)} chars)")
    except Exception as e:
        print(f"[Weekly] AI skipped (will render data-only report): {e}")

    # Render
    renderer = MarkdownRenderer(str(ROOT / "output"))
    stats = {
        "本周采集": len(records),
        "去重后": len(new_records),
        "新事件": len(new_records),
        "可信度分布": grade_str,
        "独立生态覆盖": _eco_coverage(new_records),
    }
    renderer.render_weekly_report(new_records, deep_analysis=deep_analysis, stats=stats)

    print(f"[Weekly] ✅ Done — report written to output/")
    print(f"[Weekly] Top event: {new_records[0].title[:80] if new_records else 'N/A'}")


def _eco_coverage(records: list[EventRecord]) -> str:
    ecosystems: set[str] = set()
    for r in records:
        for c in r.citations:
            ecosystems.add(c.ecosystem)
    return f"{len(ecosystems)} ecosystems: {', '.join(sorted(ecosystems)[:8])}"


# ---- CLI entry ----

def main():
    parser = argparse.ArgumentParser(description="Weekly domain intelligence digest")
    parser.add_argument(
        "--mode", choices=["weekly", "daily"], default="weekly",
        help="Run mode: weekly (full pipeline) or daily (Tier 1 only)",
    )
    args = parser.parse_args()

    # Ensure root in path for absolute imports
    sys.path.insert(0, str(ROOT))

    config = load_config()
    print(f"[Main] Mode: {args.mode} | Sources: {len(config.get('sources', {}))}")

    if args.mode == "weekly":
        run_weekly(config)
    else:
        print("[Main] Daily mode not yet configured — use weekly.")


if __name__ == "__main__":
    main()
