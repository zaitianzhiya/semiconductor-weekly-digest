"""Orchestrator: collect → filter → score → AI → render pipeline."""

import argparse
import json
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


def _generate_cn_titles(records: list[EventRecord]) -> None:
    """Generate Chinese titles for event records.

    Strategy:
      1. Try LLM batch translation (Gemini/DeepSeek/OpenAI) — best quality
      2. Fall back to structured template-based translation — always works, decent quality
         for semiconductor domain patterns.
    """
    # ---- Structured template translation ----
    # These patterns cover 80%+ of common semiconductor news title structures.
    # Each pattern: (regex, replacement template) applied in order.
    _PATTERNS: list[tuple[str, str]] = [
        # Company/entity announcements
        (r'^(.+?) Announces (.+)$', r'\1 宣布 \2'),
        (r'^(.+?) Unveils (.+)$', r'\1 发布 \2'),
        (r'^(.+?) Launches (.+)$', r'\1 推出 \2'),
        (r'^(.+?) Targets (.+)$', r'\1 瞄准 \2'),
        (r'^(.+?) Completes (.+)$', r'\1 完成 \2'),
        (r'^(.+?) Unveiled (.+)$', r'\1 发布 \2'),
        (r'^(.+?) Reportedly (.+)$', r'据报道：\1 \2'),
        # Rankings / lists
        (r'^Ranked: (.+)$', r'排名：\1'),
        (r'^Best (.+)$', r'最佳\1'),
        (r'^Top (\d+) (.+)$', r'TOP \1 \2'),
        # Market / industry reports
        (r'^(.+?) Market to Reach (.+?) by (\d{4})$', r'\1 市场规模预计到 \3 年达到 \2'),
        (r'^(.+?) Industry Poised for (.+)$', r'\1 产业有望实现 \2'),
        (r'^(.+?) Industry Closes in on (.+)$', r'\1 产业逼近 \2'),
        (r'^(.+?) Market (.+)$', r'\1 市场 \2'),
        (r'^(.+?) Soars to (.+)$', r'\1 飙升至 \2'),
        (r'^(.+?) Surges (.+)$', r'\1 暴涨 \2'),
        (r'^(.+?) Sees (.+)$', r'\1 预计 \2'),
        # Stock / financial
        (r'^(.+?) Reports (.+?) Loss(.*)$', r'\1 报告亏损 \2\3'),
        (r'^(.+?) Bets on (.+)$', r'\1 押注 \2'),
        (r'^(.+?) Stock (.+)$', r'\1 股票 \2'),
        # Analysis / opinion
        (r'^(.+?) Says (.+)$', r'\1 表示：\2'),
        (r'^(.+?) Why (.+?)\?$', r'为什么\2？\1 分析'),
        (r'^(.+?) Could (.+)$', r'\1 或将 \2'),
        # Generic X → Y
        (r'^(.+?) Shifts? (.+?) to (.+)$', r'\1 将 \2 转向 \3'),
        (r'^(.+?) Signals? (.+)$', r'\1 释放信号：\2'),
        (r'^(.+?) Hits? (.+)$', r'\1 达到 \2'),
        (r'^(.+?) Drops? (.+)$', r'\1 下跌 \2'),
        (r'^(.+?) Falls? (.+)$', r'\1 下跌 \2'),
        (r'^(.+?) Rise?s? (.+)$', r'\1 上涨 \2'),
        (r'^(.+?) Grows? (.+)$', r'\1 增长 \2'),
        (r'^(.+?) Reveals (.+)$', r'\1 透露 \2'),
        (r'^(.+?) Expands? (.+)$', r'\1 拓展 \2'),
        (r'^(.+?) Sets? (.+)$', r'\1 设定 \2'),
        (r'^(.+?) Joins (.+)$', r'\1 加入 \2'),
        (r'^(.+?) Signs? (.+)$', r'\1 签署 \2'),
        (r'^(.+?) Partners? with (.+)$', r'\1 与 \2 达成合作'),
        (r'^(.+?) Acquires? (.+)$', r'\1 收购 \2'),
        (r'^(.+?) Merges? with (.+)$', r'\1 与 \2 合并'),
        # Various prepositional patterns
        (r'^(.+?) as (.+)$', r'\1，因 \2'),
        (r'^(.+?) amid (.+)$', r'\1，在 \2 背景下'),
        (r'^(.+?) after (.+)$', r'\1，在 \2 之后'),
        (r'^(.+?) ahead of (.+)$', r'\1，\2 前夕'),
        # Weekly / daily roundups
        (r'^(.+?) Weekly (.+)$', r'\1 周报：\2'),
        (r'^(.+?) Roundup: (.+)$', r'\1 汇总：\2'),
        (r'^(.+?) Update: (.+)$', r'\1 更新：\2'),
    ]

    # Company name → Chinese mapping (order matters: longer first)
    _COMPANY_CN: list[tuple[str, str]] = [
        ("Advanced Micro Devices", "AMD"),
        ("Semiconductor Industry Association", "半导体行业协会(SIA)"),
        ("Samsung Electronics", "三星电子"),
        ("SK Hynix", "SK海力士"), ("SK hynix", "SK海力士"),
        ("Micron Technology", "美光科技"),
        ("Applied Materials", "应用材料"),
        ("Lam Research", "泛林半导体"),
        ("Qualcomm", "高通"), ("Broadcom", "博通"),
        ("NVIDIA", "英伟达"), ("Nvidia", "英伟达"),
        ("TSMC", "台积电"), ("Intel", "英特尔"),
        ("AMD", "AMD"), ("ASML", "阿斯麦"),
        ("Samsung", "三星"), ("Micron", "美光"),
        ("Arm ", "ARM "), ("CXMT", "长鑫存储"),
        ("SMIC", "中芯国际"), ("YMTC", "长江存储"),
        ("Hua Hong", "华虹半导体"),
        ("KLA", "科磊"), ("Cadence", "Cadence"),
        ("Synopsys", "新思科技"), ("Rapidus", "Rapidus"),
        ("Navitas Semiconductor", "纳微半导体"),
        ("ChangXin Memory", "长鑫存储"),
        ("Lattice", "莱迪思半导体"),
        ("Kingston", "金士顿"),
        ("Tesla", "特斯拉"), ("Apple", "苹果"),
    ]

    # Domain term → Chinese (standalone terms that aren't just word pieces)
    _TERM_CN: list[tuple[str, str]] = [
        ("Semiconductor Industry", "半导体产业"),
        ("Semiconductor", "半导体"),
        ("semiconductor", "半导体"),
        ("semiconductors", "半导体"),
        ("Chip", "芯片"), ("chip", "芯片"), ("chips", "芯片"),
        ("Foundry", "晶圆代工"), ("foundry", "晶圆代工"),
        ("Memory", "存储器"), ("memory", "存储器"),
        ("Processor", "处理器"),
        ("Equipment", "设备"),
        ("Packaging", "封装"), ("packaging", "封装"),
        ("Manufacturing", "制造"),
        ("Technology", "技术"), ("technology", "技术"),
        ("Industry", "产业"), ("Market", "市场"),
        ("Revenue", "营收"), ("Investment", "投资"),
        ("Supply Chain", "供应链"), ("Data Center", "数据中心"),
        ("AI Chip", "AI芯片"), ("AI chip", "AI芯片"),
        ("GPU", "GPU"), ("CPU", "CPU"), ("NPU", "NPU"),
        ("HBM4", "HBM4"), ("HBM3", "HBM3"), ("HBM3e", "HBM3e"),
        ("HBM", "HBM"), ("DRAM", "DRAM"), ("NAND", "NAND"),
        ("EUV", "EUV光刻"), ("DUV", "DUV光刻"),
        ("2nm", "2nm"), ("3nm", "3nm"), ("5nm", "5nm"),
        ("CoWoS", "CoWoS先进封装"), ("Chiplet", "Chiplet"),
        ("RISC-V", "RISC-V"), ("GAA", "GAA晶体管"),
        ("Advanced Packaging", "先进封装"),
        ("advanced packaging", "先进封装"),
        ("Kospi", "韩国KOSPI指数"),
        ("Korea", "韩国"), ("Japan", "日本"), ("China", "中国"),
        ("U.S. ", "美国"), ("US ", "美国"),
        ("IPO", "上市"), ("Stock", "股票"), ("stocks", "股票"),
        ("Revenue", "营收"), ("Earnings", "盈利"),
        ("Production", "量产"), ("production", "量产"),
        ("Collaboration", "合作"), ("Innovation", "创新"),
        ("Breakthrough", "突破"),
        ("Milestone", "里程碑"), ("Bottleneck", "瓶颈"),
        ("Billions", "数十亿"), ("Trillion", "万亿"),
        ("Report", "报告"), ("Analysis", "分析"),
        ("Update", "更新"), ("Outlook", "展望"),
        ("Trends", "趋势"),
        ("Q1 ", "第一季度"), ("Q2 ", "第二季度"),
        ("Q3 ", "第三季度"), ("Q4 ", "第四季度"),
        ("H1 ", "上半年"), ("H2 ", "下半年"),
    ]

    import re

    for r in records:
        en = r.title.strip()

        # Step 1: Try structured pattern matching
        cn = None
        for pattern, template in _PATTERNS:
            m = re.match(pattern, en)
            if m:
                cn = template
                # Fill placeholders
                for gi in range(1, len(m.groups()) + 1):
                    # Apply term/company substitutions within each group
                    group_text = m.group(gi)
                    for term, cn_term in _COMPANY_CN:
                        group_text = group_text.replace(term, cn_term)
                    for term, cn_term in _TERM_CN:
                        group_text = group_text.replace(term, cn_term)
                    cn = cn.replace(f"\\{gi}", group_text)
                break

        # Step 2: Fallback — term substitution only
        if cn is None:
            cn = en
            for term, cn_term in _COMPANY_CN:
                cn = cn.replace(term, cn_term)
            for term, cn_term in _TERM_CN:
                cn = cn.replace(term, cn_term)

        # Step 3: Clean up — remove none/None artifacts, collapse whitespace
        cn = re.sub(r'\bNone\b', '', cn)
        cn = re.sub(r'\s{2,}', ' ', cn).strip()

        # Only use CN if it's actually different from EN
        r.title_cn = cn if cn != en else ""

    # ---- Try LLM batch translation for top events (better quality) ----
    try:
        from src.ai.llm_client import LLMClient
        client = LLMClient()
    except Exception:
        return

    top_titles = [(r.event_id, r.title) for r in records[:30]
                  if r.confidence_grade in ("A", "B", "C")]
    if not top_titles:
        return

    prompt = (
        "请将以下半导体行业新闻标题翻译为简洁流畅的中文（一行一条，保持专业术语不翻译）：\n\n"
        + "\n".join(f"{i+1}. {t}" for i, (_, t) in enumerate(top_titles))
        + "\n\n请严格按编号返回，格式：1. 中文翻译"
    )

    try:
        result = client.chat(
            "你是半导体行业专业翻译。请将英文新闻标题翻译为流畅简洁的中文，保持专业术语(EUV/DUV/GAA/HBM/CoWoS等)不翻。",
            prompt, temperature=0.2,
        )
        id_to_cn: dict[str, str] = {}
        for line in result.strip().split("\n"):
            line = line.strip()
            parts = line.split(". ", 1)
            if len(parts) == 2 and parts[0].isdigit():
                idx = int(parts[0]) - 1
                if 0 <= idx < len(top_titles):
                    id_to_cn[top_titles[idx][0]] = parts[1].strip()

        for r in records:
            if r.event_id in id_to_cn and id_to_cn[r.event_id]:
                r.title_cn = id_to_cn[r.event_id]
    except Exception as e:
        print(f"  [CN translate] LLM batch failed: {e}, using template fallback")
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

    # Generate Chinese titles (LLM batch translation with rule-based fallback)
    _generate_cn_titles(new_records)
    cn_count = sum(1 for r in new_records if r.title_cn)
    print(f"[Weekly] CN titles generated: {cn_count}/{len(new_records)}")

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
